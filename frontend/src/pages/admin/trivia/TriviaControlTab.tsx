import { useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { startTrivia, advanceQuestion } from '../../../api/gameplayApi';
import { useTriviaEvents } from '../../../hooks/useTriviaEvents';
import { TriviaRanking, CurrentQuestion } from '../../../types';
import type { AdminLobbyDTO } from '../../../types/adminLobby';

interface TriviaControlTabProps {
  triviaId: string;
  triviaStatus?: 'DRAFT' | 'LOBBY' | 'IN_PROGRESS' | 'FINISHED';
  onStatusUpdate?: () => void;
}

export default function TriviaControlTab({
  triviaId,
  triviaStatus,
  onStatusUpdate,
}: TriviaControlTabProps) {
  const { user } = useAuth();
  const [ranking, setRanking] = useState<TriviaRanking | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<CurrentQuestion | null>(null);
  const [lobbyData, setLobbyData] = useState<AdminLobbyDTO | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  // Use SSE events instead of polling
  useTriviaEvents({
    triviaId,
    userId: user?.id,
    role: 'ADMIN',
    enabled: !!triviaId,
    onAdminLobbyUpdated: (data) => {
      setLobbyData(data);
    },
    onRankingUpdated: (data) => {
      // Map SSE ranking format to TriviaRanking format
      setRanking({
        trivia_id: data.trivia_id,
        entries: data.entries.map((entry) => ({
          user_id: entry.user_id,
          user_name: entry.name,
          score: entry.score,
          position: entry.position,
        })),
      });
    },
    onCurrentQuestionUpdated: (data) => {
      // Map SSE current question format to CurrentQuestion format
      setCurrentQuestion({
        question_id: data.question_id,
        question_text: data.text,
        options: data.options.map((opt) => ({
          id: opt.id,
          text: opt.text,
        })),
        time_remaining_seconds: data.remaining_seconds,
        current_question_index: data.question_index,
        total_questions: data.total_questions,
      });
    },
  });

  const [startInFlight, setStartInFlight] = useState(false);
  const [nextInFlight, setNextInFlight] = useState(false);

  const handleStartTrivia = async () => {
    if (!triviaId || !user || startInFlight) return;
    setStartInFlight(true);
    setActionLoading(true);
    setActionError(null);
    const response = await startTrivia(triviaId, user.id);
    if (response.error) {
      // Check if it's a 409 conflict error
      if (response.error.includes('409') || response.error.includes('Cannot start trivia')) {
        setActionError(response.error);
      } else {
        setActionError(response.error);
      }
    } else if (response.data) {
      // Status will be updated via SSE
      if (onStatusUpdate) {
        onStatusUpdate();
      }
    }
    setActionLoading(false);
    setStartInFlight(false);
  };

  // Determine if start button should be enabled
  const isLobbyOrDraft = triviaStatus === 'LOBBY' || triviaStatus === 'DRAFT';
  const canStart = lobbyData && 
    lobbyData.present_count === lobbyData.assigned_count && 
    lobbyData.ready_count === lobbyData.assigned_count &&
    isLobbyOrDraft;
  
  const missingPlayers = lobbyData ? lobbyData.assigned_count - lobbyData.present_count : 0;

  const handleNextQuestion = async () => {
    if (!triviaId || !user || nextInFlight) return;
    setNextInFlight(true);
    setActionLoading(true);
    setActionError(null);
    const response = await advanceQuestion(triviaId, user.id);
    if (response.error) {
      setActionError(response.error);
    } else if (response.data) {
      // Status will be updated via SSE
      if (onStatusUpdate) {
        onStatusUpdate();
      }
    }
    setActionLoading(false);
    setNextInFlight(false);
  };

  return (
    <div>
      <h4 className="mb-4">Control</h4>

      {actionError && (
        <div className="alert alert-danger mb-3">{actionError}</div>
      )}

      {/* Lobby Status Section */}
      {(triviaStatus === 'LOBBY' || triviaStatus === 'DRAFT') && (
        <div className="card mb-4 fade-in">
          <div className="card-body">
            <h5 className="card-title mb-3">Estado del Lobby</h5>

            {lobbyData && (
              <>
                <div className="d-flex gap-4 mb-3">
                  <div>
                    <strong>Presentes: {lobbyData.present_count} / {lobbyData.assigned_count}</strong>
                  </div>
                  <div>
                    <strong>Listos: {lobbyData.ready_count} / {lobbyData.assigned_count}</strong>
                  </div>
                </div>

                {lobbyData.players.length > 0 && (
                  <div className="mt-3">
                    <h6 className="mb-3">Jugadores</h6>
                    <div className="d-flex flex-column gap-2">
                      {lobbyData.players.map((player) => (
                        <div
                          key={player.user_id}
                          className="d-flex justify-content-between align-items-center p-2 bg-light rounded fade-in"
                        >
                          <span className="fw-bold">{player.name}</span>
                          <div className="d-flex gap-2">
                            <span
                              className={`badge ${player.present ? 'bg-success' : 'bg-warning'}`}
                            >
                              {player.present ? '✅ Presente' : '⏳ Esperando'}
                            </span>
                            <span
                              className={`badge ${player.ready ? 'bg-success' : 'bg-warning'}`}
                            >
                              {player.ready ? '✅ Listo' : '⏳ No listo'}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}

      <div className="mb-4 d-flex flex-column gap-2">
        <div className="d-flex gap-2">
          <button
            onClick={handleStartTrivia}
            disabled={startInFlight || actionLoading || !canStart || !isLobbyOrDraft}
            className={`btn btn-animated ${startInFlight || actionLoading || !canStart || !isLobbyOrDraft ? 'btn-secondary' : 'btn-success'}`}
          >
            {startInFlight || actionLoading ? 'Procesando...' : 'Iniciar trivia'}
          </button>
          <button
            onClick={handleNextQuestion}
            disabled={nextInFlight || actionLoading || triviaStatus !== 'IN_PROGRESS'}
            className={`btn btn-animated ${nextInFlight || actionLoading || triviaStatus !== 'IN_PROGRESS' ? 'btn-secondary' : 'btn-primary'}`}
          >
            {nextInFlight || actionLoading ? 'Procesando...' : 'Siguiente pregunta'}
          </button>
        </div>
        
        {/* Status message for start button */}
        {!canStart && (triviaStatus === 'LOBBY' || triviaStatus === 'DRAFT') && lobbyData && (
          <div className="alert alert-warning">
            {missingPlayers > 0 ? (
              <span>Faltan {missingPlayers} jugador{missingPlayers > 1 ? 'es' : ''} por entrar al lobby.</span>
            ) : lobbyData.present_count === lobbyData.assigned_count && lobbyData.ready_count !== lobbyData.assigned_count ? (
              <span>Esperando que todos los jugadores estén listos.</span>
            ) : (
              <span>Esperando que todos los jugadores asignados estén presentes y listos.</span>
            )}
          </div>
        )}
      </div>

      {currentQuestion && (
        <div className="card mb-4 fade-in">
          <div className="card-body">
            <h5 className="card-title">Pregunta Actual</h5>
            <p className="mb-2">
              <strong>Pregunta {currentQuestion.current_question_index + 1} de {currentQuestion.total_questions}</strong>
            </p>
            <p className="fs-5 mb-3">{currentQuestion.question_text}</p>
            <ul className="list-unstyled">
              {currentQuestion.options.map((option) => (
                <li key={option.id} className="p-2 mb-2 bg-light rounded">
                  {option.text}
                </li>
              ))}
            </ul>
            {currentQuestion.time_remaining_seconds !== undefined && (
              <p className="text-muted mt-3 mb-0">
                Tiempo restante: {currentQuestion.time_remaining_seconds}s
              </p>
            )}
          </div>
        </div>
      )}

      <div>
        <h5 className="mb-3">Ranking en Vivo</h5>
        {!ranking ? (
          <div className="text-center text-muted py-4">Cargando ranking...</div>
        ) : ranking.entries.length === 0 ? (
          <div className="text-center text-muted py-4">
            No hay datos de ranking disponibles. Los jugadores necesitan enviar respuestas para ver puntajes.
          </div>
        ) : (
          <div className="card fade-in">
            <div className="table-responsive">
              <table className="table align-middle mb-0">
                <thead>
                  <tr>
                    <th>Posición</th>
                    <th>Jugador</th>
                    <th>Puntaje</th>
                  </tr>
                </thead>
                <tbody>
                  {ranking.entries.map((entry) => (
                    <tr key={entry.user_id}>
                      <td>{entry.position}</td>
                      <td>{entry.user_name}</td>
                      <td>{entry.score}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
