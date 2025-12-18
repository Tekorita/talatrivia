/** Player API service for TalaTrivia. */
import { get, post } from './api';
import type {
  LobbyDTO,
  TriviaStatusDTO,
  CurrentQuestionDTO,
  SubmitAnswerDTO,
  SubmitAnswerResponseDTO,
  RankingRowDTO,
} from '../types/player';
import type { Trivia } from '../types';

export interface AssignedTrivia {
  trivia_id: string;
  title: string;
  description: string;
  status: 'DRAFT' | 'LOBBY' | 'IN_PROGRESS' | 'FINISHED';
}

/**
 * Join a trivia.
 */
export async function joinTrivia(triviaId: string, userId: string): Promise<{ data?: unknown; error?: string }> {
  return post(`/trivias/${triviaId}/join`, { user_id: userId });
}

/**
 * Set player as ready.
 */
export async function setReady(triviaId: string, userId: string): Promise<{ data?: unknown; error?: string }> {
  return post(`/trivias/${triviaId}/ready`, { user_id: userId });
}

/**
 * Get lobby information (list of players).
 * Uses the dedicated player lobby endpoint.
 */
export async function getLobby(triviaId: string): Promise<{ data?: LobbyDTO; error?: string }> {
  return get<LobbyDTO>(`/play/trivias/${triviaId}/lobby`);
}

/**
 * Update player heartbeat (last_seen_at).
 */
export async function updateHeartbeat(triviaId: string, userId: string): Promise<{ error?: string }> {
  const response = await post(`/play/trivias/${triviaId}/heartbeat`, { user_id: userId });
  if (response.error) {
    return { error: response.error };
  }
  return {};
}

/**
 * Get trivias assigned to a user.
 */
export async function getAssignedTrivias(userId: string): Promise<{ data?: AssignedTrivia[]; error?: string }> {
  return get<AssignedTrivia[]>(`/play/trivias/assigned?user_id=${userId}`);
}

/**
 * Get trivia status.
 * Uses the trivia detail endpoint and adapts the response.
 */
export async function getStatus(triviaId: string): Promise<{ data?: TriviaStatusDTO; error?: string }> {
  const response = await get<Trivia>(`/trivias/${triviaId}`);
  
  if (response.error) {
    return { error: response.error };
  }
  
  if (!response.data) {
    return { error: 'Trivia not found' };
  }
  
  // Map trivia status to game state
  let state: TriviaStatusDTO['state'] = 'WAITING';
  if (response.data.status === 'IN_PROGRESS') {
    state = 'IN_PROGRESS';
  } else if (response.data.status === 'FINISHED') {
    state = 'FINISHED';
  }
  
  return {
    data: {
      state,
      current_question_index: response.data.current_question_index,
    },
  };
}

/**
 * Get current question for a trivia.
 */
export async function getCurrentQuestion(
  triviaId: string,
  userId: string
): Promise<{ data?: CurrentQuestionDTO; error?: string }> {
  // Get question data
  const questionResponse = await get<{
    question_id: string;
    question_text: string;
    options: Array<{ option_id: string; option_text: string }>;
    time_remaining_seconds: number;
  }>(`/trivias/${triviaId}/current-question?user_id=${userId}`);
  
  if (questionResponse.error) {
    return { error: questionResponse.error };
  }
  
  if (!questionResponse.data) {
    return { error: 'Current question not found' };
  }
  
  // Get status for question_index
  const statusResponse = await getStatus(triviaId);
  const questionIndex = statusResponse.data?.current_question_index ?? 0;
  
  // Get total questions count
  const questionsResponse = await get<Array<{ id: string; text: string; difficulty: string }>>(
    `/trivias/${triviaId}/questions`
  );
  const totalQuestions = questionsResponse.data?.length ?? 0;
  
  return {
    data: {
      question_id: questionResponse.data.question_id,
      text: questionResponse.data.question_text,
      options: questionResponse.data.options.map((opt) => ({
        id: opt.option_id,
        text: opt.option_text,
      })),
      remaining_seconds: questionResponse.data.time_remaining_seconds,
      question_index: questionIndex,
      total_questions: totalQuestions,
    },
  };
}

/**
 * Submit an answer.
 */
export async function submitAnswer(
  triviaId: string,
  userId: string,
  payload: SubmitAnswerDTO
): Promise<{ data?: SubmitAnswerResponseDTO; error?: string }> {
  const response = await post<{
    trivia_id: string;
    question_id: string;
    selected_option_id: string;
    is_correct: boolean;
    earned_points: number;
    total_score: number;
    time_remaining_seconds: number;
  }>(`/trivias/${triviaId}/answer`, {
    user_id: userId,
    selected_option_id: payload.option_id,
  });
  
  if (response.error) {
    // Check if it's a conflict (already answered)
    if (response.error.includes('409') || response.error.includes('already')) {
      return {
        data: {
          accepted: false,
          already_answered: true,
        },
      };
    }
    return { error: response.error };
  }
  
  return {
    data: {
      accepted: true,
    },
  };
}

/**
 * Get ranking for a trivia.
 */
export async function getRanking(triviaId: string): Promise<{ data?: RankingRowDTO[]; error?: string }> {
  const response = await get<{
    trivia_id: string;
    status: string;
    ranking: Array<{
      position: number;
      user_id: string;
      user_name: string;
      score: number;
    }>;
  }>(`/trivias/${triviaId}/ranking`);
  
  if (response.error) {
    return { error: response.error };
  }
  
  if (!response.data) {
    return { data: [] };
  }
  
  return {
    data: response.data.ranking.map((entry) => ({
      user_id: entry.user_id,
      name: entry.user_name,
      score: entry.score,
      position: entry.position,
    })),
  };
}
