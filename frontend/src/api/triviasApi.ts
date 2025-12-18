/** Trivias API service. */
import { get, post } from './api';
import { Trivia, Question, User } from '../types';
import type { AdminLobbyDTO } from '../types/adminLobby';

export interface CreateTriviaRequest {
  title: string;
  description: string;
  user_ids: string[];
  question_ids?: string[]; // Optional - questions are added from Trivia Detail
}

export interface CreateTriviaResponse {
  id: string;
  title: string;
  description: string;
  created_by_user_id: string;
  status: 'LOBBY' | 'IN_PROGRESS' | 'FINISHED';
}

/**
 * Get all trivias.
 */
export async function getTrivias(): Promise<{ data?: Trivia[]; error?: string }> {
  return get<Trivia[]>('/trivias');
}

/**
 * Create a new trivia.
 */
export async function createTrivia(
  triviaData: CreateTriviaRequest
): Promise<{ data?: CreateTriviaResponse; error?: string }> {
  return post<CreateTriviaResponse>('/trivias', triviaData);
}

/**
 * Get trivia by ID.
 */
export async function getTriviaById(triviaId: string): Promise<{ data?: Trivia; error?: string }> {
  return get<Trivia>(`/trivias/${triviaId}`);
}

/**
 * List questions associated with a trivia.
 */
export async function listTriviaQuestions(
  triviaId: string
): Promise<{ data?: Question[]; error?: string }> {
  return get<Question[]>(`/trivias/${triviaId}/questions`);
}

/**
 * Add a question to a trivia.
 */
export async function addQuestionToTrivia(
  triviaId: string,
  questionId: string
): Promise<{ data?: { question_id: string }; error?: string }> {
  return post<{ question_id: string }>(`/trivias/${triviaId}/questions`, { question_id: questionId });
}

/**
 * List players associated with a trivia.
 */
export async function listTriviaPlayers(
  triviaId: string
): Promise<{ data?: User[]; error?: string }> {
  return get<User[]>(`/trivias/${triviaId}/players`);
}

/**
 * Add a player to a trivia.
 */
export async function addPlayerToTrivia(
  triviaId: string,
  userId: string
): Promise<{ data?: { user_id: string }; error?: string }> {
  return post<{ user_id: string }>(`/trivias/${triviaId}/players`, { user_id: userId });
}

/**
 * Reset a trivia: set to LOBBY, clear answers, reset scores.
 */
export async function resetTrivia(
  triviaId: string
): Promise<{ data?: { status: string }; error?: string }> {
  return post<{ status: string }>(`/trivias/${triviaId}/reset`, {});
}

/**
 * Get admin lobby information for a trivia.
 */
export async function getAdminLobby(
  triviaId: string
): Promise<{ data?: AdminLobbyDTO; error?: string }> {
  return get<AdminLobbyDTO>(`/admin/trivias/${triviaId}/lobby`);
}
