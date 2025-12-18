/** Admin lobby types for TalaTrivia. */

export interface AdminLobbyPlayerDTO {
  user_id: string;
  name: string;
  present: boolean;
  ready: boolean;
}

export interface AdminLobbyDTO {
  assigned_count: number;
  present_count: number;
  ready_count: number;
  players: AdminLobbyPlayerDTO[];
}
