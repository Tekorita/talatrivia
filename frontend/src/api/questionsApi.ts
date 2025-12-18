/** Questions API service. */
import { get, post } from './api';
import { Question } from '../types';

export interface CreateQuestionRequest {
  text: string;
  difficulty: 'EASY' | 'MEDIUM' | 'HARD';
  options: Array<{
    text: string;
    is_correct: boolean;
  }>;
}

export interface CreateQuestionResponse {
  id: string;
  text: string;
  difficulty: 'EASY' | 'MEDIUM' | 'HARD';
  created_by_user_id: string;
}

/**
 * Get all questions.
 */
export async function getQuestions(): Promise<{ data?: Question[]; error?: string }> {
  return get<Question[]>('/questions');
}

/**
 * Create a new question.
 */
export async function createQuestion(
  questionData: CreateQuestionRequest
): Promise<{ data?: CreateQuestionResponse; error?: string }> {
  return post<CreateQuestionResponse>('/questions', questionData);
}
