/** Users API service. */
import { get, post } from './api';
import { User } from '../types';

export interface CreateUserRequest {
  name: string;
  email: string;
  password: string;
  role?: 'ADMIN' | 'PLAYER';
}

export interface CreateUserResponse {
  id: string;
  name: string;
  email: string;
  role: 'ADMIN' | 'PLAYER';
}

/**
 * Get all users.
 */
export async function getUsers(): Promise<{ data?: User[]; error?: string }> {
  return get<User[]>('/users');
}

/**
 * Create a new user.
 */
export async function createUser(
  userData: CreateUserRequest
): Promise<{ data?: CreateUserResponse; error?: string }> {
  return post<CreateUserResponse>('/users', userData);
}
