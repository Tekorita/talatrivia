/** Gameplay API service. */
import { get, post } from './api';
import { TriviaRanking, CurrentQuestion } from '../types';

export interface StartTriviaRequest {
  admin_user_id: string;
}

export interface StartTriviaResponse {
  trivia_id: string;
  trivia_status: 'IN_PROGRESS' | 'FINISHED';
  started_at: string;
  current_question_index: number;
}

export interface AdvanceQuestionResponse {
  trivia_id: string;
  trivia_status: 'IN_PROGRESS' | 'FINISHED';
  current_question_index: number;
}

/**
 * Start a trivia.
 */
export async function startTrivia(
  triviaId: string,
  adminUserId: string
): Promise<{ data?: StartTriviaResponse; error?: string }> {
  return post<StartTriviaResponse>(`/trivias/${triviaId}/start`, {
    admin_user_id: adminUserId,
  });
}

/**
 * Advance to next question.
 */
export async function advanceQuestion(
  triviaId: string,
  adminUserId: string
): Promise<{ data?: AdvanceQuestionResponse; error?: string }> {
  return post<AdvanceQuestionResponse>(`/trivias/${triviaId}/next-question`, {
    admin_user_id: adminUserId,
  });
}

/**
 * Get trivia ranking.
 */
export async function getTriviaRanking(
  triviaId: string
): Promise<{ data?: TriviaRanking; error?: string }> {
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
    return { data: { trivia_id: triviaId, entries: [] } };
  }
  
  // Map backend response to frontend format
  return {
    data: {
      trivia_id: response.data.trivia_id,
      entries: response.data.ranking.map((entry) => ({
        user_id: entry.user_id,
        user_name: entry.user_name,
        score: entry.score,
        position: entry.position,
      })),
    },
  };
}

/**
 * Get current question.
 */
export async function getCurrentQuestion(
  triviaId: string,
  userId: string
): Promise<{ data?: CurrentQuestion; error?: string }> {
  return get<CurrentQuestion>(`/trivias/${triviaId}/current-question?user_id=${userId}`);
}
