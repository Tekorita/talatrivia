/** Player flow types for TalaTrivia. */

export type TriviaGameState = 'WAITING' | 'IN_PROGRESS' | 'FINISHED';

export interface TriviaStatusDTO {
  state: TriviaGameState;
  current_question_index?: number;
  total_players?: number;
  ready_players?: number;
  assigned_players?: number;
}

export interface LobbyPlayerDTO {
  user_id: string;
  name: string;
  present: boolean;
  ready: boolean;
}

export interface LobbyDTO {
  players: LobbyPlayerDTO[];
}

export interface QuestionOptionDTO {
  id: string;
  text: string;
}

export interface CurrentQuestionDTO {
  question_id: string;
  text: string;
  options: QuestionOptionDTO[];
  remaining_seconds: number;
  question_index: number;
  total_questions: number;
}

export interface SubmitAnswerDTO {
  question_id: string;
  option_id: string;
}

export interface SubmitAnswerResponseDTO {
  accepted: boolean;
  already_answered?: boolean;
}

export interface RankingRowDTO {
  user_id: string;
  name: string;
  score: number;
  position?: number;
}
