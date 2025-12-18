/** Shared TypeScript types for TalaTrivia. */

export type UserRole = 'ADMIN' | 'PLAYER';

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  created_at?: string;
}

export type QuestionDifficulty = 'EASY' | 'MEDIUM' | 'HARD';

export interface Option {
  id: string;
  text: string;
  is_correct: boolean;
  question_id?: string;
}

export interface Question {
  id: string;
  text: string;
  difficulty: QuestionDifficulty;
  created_by_user_id?: string;
  created_at?: string;
  options?: Option[];
}

export interface Trivia {
  id: string;
  title: string;
  description: string;
  created_by_user_id: string;
  status: 'DRAFT' | 'LOBBY' | 'IN_PROGRESS' | 'FINISHED';
  current_question_index: number;
  started_at?: string;
  created_at?: string;
}

export interface RankingEntry {
  user_id: string;
  user_name: string;
  score: number;
  position?: number;
}

export interface TriviaRanking {
  trivia_id: string;
  entries: RankingEntry[];
}

export interface CurrentQuestion {
  question_id: string;
  question_text: string;
  options: Array<{
    id: string;
    text: string;
  }>;
  time_remaining_seconds?: number;
  current_question_index: number;
  total_questions: number;
}
