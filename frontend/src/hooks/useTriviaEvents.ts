import { useEffect, useRef, useState } from 'react';
import { post } from '../api/api';
import type { AdminLobbyDTO } from '../types/adminLobby';
import type {
  CurrentQuestionDTO,
  LobbyDTO,
  RankingRowDTO,
  TriviaStatusDTO,
} from '../types/player';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface UseTriviaEventsOptions {
  triviaId: string;
  userId?: string;
  role?: 'ADMIN' | 'PLAYER';
  onLobbyUpdated?: (data: LobbyDTO) => void;
  onAdminLobbyUpdated?: (data: AdminLobbyDTO) => void;
  onStatusUpdated?: (data: TriviaStatusDTO) => void;
  onCurrentQuestionUpdated?: (data: CurrentQuestionDTO) => void | Promise<void>;
  onRankingUpdated?: (data: { trivia_id: string; entries: RankingRowDTO[] }) => void;
  enabled?: boolean;
}

interface TicketResponse {
  ticket: string;
  expires_in: number;
}

/**
 * Hook to connect to SSE stream for trivia events.
 * Handles ticket-based authentication and event parsing.
 */
export function useTriviaEvents(options: UseTriviaEventsOptions) {
  const {
    triviaId,
    userId,
    onLobbyUpdated,
    onAdminLobbyUpdated,
    onStatusUpdated,
    onCurrentQuestionUpdated,
    onRankingUpdated,
    enabled = true,
  } = options;

  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const ticketRef = useRef<string | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;

  // Cleanup function
  const cleanup = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    ticketRef.current = null;
    reconnectAttemptsRef.current = 0;
  };

  // Get ticket and connect to SSE
  const connect = async () => {
    if (!enabled || !triviaId) {
      return;
    }

    try {
      // Get ticket
      const ticketResponse = await post<TicketResponse>(
        `/trivias/${triviaId}/events/token`,
        {
          user_id: userId || null,
        }
      );

      if (ticketResponse.error || !ticketResponse.data) {
        throw new Error(ticketResponse.error || 'Failed to get SSE ticket');
      }

      ticketRef.current = ticketResponse.data.ticket;

      // Connect to SSE stream
      const eventSource = new EventSource(
        `${API_BASE_URL}/trivias/${triviaId}/events?ticket=${ticketRef.current}`
      );
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        setConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
      };

      eventSource.onerror = (err) => {
        console.error('SSE connection error:', err);
        setConnected(false);
        
        // Try to reconnect if not exceeded max attempts
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current += 1;
          reconnectTimeoutRef.current = setTimeout(() => {
            cleanup();
            connect();
          }, 2000 * reconnectAttemptsRef.current); // Exponential backoff
        } else {
          setError('Failed to connect to events stream after multiple attempts');
        }
      };

      // Handle events
      eventSource.addEventListener('connected', (event) => {
        const data = JSON.parse(event.data);
        console.log('SSE connected:', data);
      });

      eventSource.addEventListener('lobby_updated', (event) => {
        try {
          const data = JSON.parse(event.data) as LobbyDTO;
          onLobbyUpdated?.(data);
        } catch (err) {
          console.error('Error parsing lobby_updated event:', err);
        }
      });

      eventSource.addEventListener('admin_lobby_updated', (event) => {
        try {
          const data = JSON.parse(event.data) as AdminLobbyDTO;
          onAdminLobbyUpdated?.(data);
        } catch (err) {
          console.error('Error parsing admin_lobby_updated event:', err);
        }
      });

      eventSource.addEventListener('status_updated', (event) => {
        try {
          const data = JSON.parse(event.data) as TriviaStatusDTO;
          onStatusUpdated?.(data);
        } catch (err) {
          console.error('Error parsing status_updated event:', err);
        }
      });

      eventSource.addEventListener('current_question_updated', async (event) => {
        try {
          const rawData = JSON.parse(event.data);
          // Map backend format to frontend format
          // Note: fifty_fifty_available is NOT in SSE events (it's player-specific)
          // The component should fetch the current question individually to get it
          const data: CurrentQuestionDTO = {
            question_id: rawData.question_id,
            text: rawData.question_text,
            options: rawData.options.map((opt: { option_id: string; option_text: string }) => ({
              id: opt.option_id,
              text: opt.option_text,
            })),
            remaining_seconds: rawData.time_remaining_seconds,
            question_index: rawData.question_index,
            total_questions: rawData.total_questions,
            // fifty_fifty_available will be undefined - component should fetch it
            fifty_fifty_available: false, // Placeholder, will be fetched individually
          };
          await onCurrentQuestionUpdated?.(data);
        } catch (err) {
          console.error('Error parsing current_question_updated event:', err);
        }
      });

      eventSource.addEventListener('ranking_updated', (event) => {
        try {
          const rawData = JSON.parse(event.data);
          // Map backend format to frontend format
          const data = {
            trivia_id: rawData.trivia_id,
            entries: rawData.ranking.map((entry: {
              position: number;
              user_id: string;
              user_name: string;
              score: number;
            }) => ({
              user_id: entry.user_id,
              name: entry.user_name,
              score: entry.score,
              position: entry.position,
            })),
          };
          onRankingUpdated?.(data);
        } catch (err) {
          console.error('Error parsing ranking_updated event:', err);
        }
      });
    } catch (err) {
      console.error('Error connecting to SSE:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
      setConnected(false);
    }
  };

  useEffect(() => {
    if (enabled && triviaId) {
      connect();
    }

    return () => {
      cleanup();
    };
  }, [enabled, triviaId, userId]);

  return { connected, error };
}

