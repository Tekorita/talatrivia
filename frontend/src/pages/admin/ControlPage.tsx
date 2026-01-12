import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useActiveTrivia } from '../../context/ActiveTriviaContext';
import { getTrivias } from '../../api/triviasApi';
import { startTrivia, advanceQuestion } from '../../api/gameplayApi';
import { useTriviaEvents } from '../../hooks/useTriviaEvents';
import { Trivia, TriviaRanking, CurrentQuestion } from '../../types';

export default function ControlPage() {
  const { user } = useAuth();
  const { activeTriviaId, setActiveTriviaId } = useActiveTrivia();
  const [trivias, setTrivias] = useState<Trivia[]>([]);
  const [ranking, setRanking] = useState<TriviaRanking | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<CurrentQuestion | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    loadTrivias();
  }, []);

  // Use SSE events instead of polling
  useTriviaEvents({
    triviaId: activeTriviaId || '',
    userId: user?.id,
    role: 'ADMIN',
    enabled: !!activeTriviaId,
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

  const loadTrivias = async () => {
    const response = await getTrivias();
    if (response.error) {
      // Silently handle errors - endpoint might not exist yet
      setTrivias([]);
    } else if (response.data) {
      setTrivias(response.data);
    }
  };

  const handleStartTrivia = async () => {
    if (!activeTriviaId || !user) return;
    setActionLoading(true);
    setActionError(null);
    const response = await startTrivia(activeTriviaId, user.id);
    if (response.error) {
      setActionError(response.error);
    } else if (response.data) {
      // Reload trivias to get updated status
      // Ranking and current question will be updated via SSE
      loadTrivias();
    }
    setActionLoading(false);
  };

  const handleNextQuestion = async () => {
    if (!activeTriviaId || !user) return;
    setActionLoading(true);
    setActionError(null);
    const response = await advanceQuestion(activeTriviaId, user.id);
    if (response.error) {
      setActionError(response.error);
    } else if (response.data) {
      // Reload trivias
      // Current question will be updated via SSE
      loadTrivias();
    }
    setActionLoading(false);
  };

  const activeTrivia = trivias.find((t) => t.id === activeTriviaId);

  return (
    <div>
      <h2>Control (Live)</h2>

      <div style={{ marginBottom: '2rem' }}>
        <label style={{ display: 'block', marginBottom: '0.5rem' }}>Active Trivia</label>
        <select
          value={activeTriviaId || ''}
          onChange={(e) => setActiveTriviaId(e.target.value || null)}
          style={{ width: '100%', maxWidth: '400px', padding: '0.75rem', border: '1px solid #ccc', borderRadius: '4px' }}
        >
          <option value="">-- Select a trivia --</option>
          {trivias.map((trivia) => (
            <option key={trivia.id} value={trivia.id}>
              {trivia.title} ({trivia.status})
            </option>
          ))}
        </select>
      </div>

      {actionError && (
        <div style={{ padding: '0.75rem', backgroundColor: '#fee', color: '#c33', borderRadius: '4px', marginBottom: '1rem' }}>
          {actionError}
        </div>
      )}

      {activeTrivia && (
        <div style={{ marginBottom: '2rem', padding: '1rem', backgroundColor: '#fff', borderRadius: '4px', border: '1px solid #ddd' }}>
          <h3>Trivia Status</h3>
          <p>
            <strong>Status:</strong> {activeTrivia.status}
          </p>
          <p>
            <strong>Current Question Index:</strong> {activeTrivia.current_question_index}
          </p>
          {activeTrivia.started_at && (
            <p>
              <strong>Started At:</strong> {new Date(activeTrivia.started_at).toLocaleString()}
            </p>
          )}
        </div>
      )}

      {activeTriviaId && (
        <div style={{ marginBottom: '2rem', display: 'flex', gap: '1rem' }}>
          <button
            onClick={handleStartTrivia}
            disabled={actionLoading || activeTrivia?.status === 'IN_PROGRESS' || activeTrivia?.status === 'FINISHED'}
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: actionLoading || activeTrivia?.status === 'IN_PROGRESS' || activeTrivia?.status === 'FINISHED' ? '#ccc' : '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: actionLoading || activeTrivia?.status === 'IN_PROGRESS' || activeTrivia?.status === 'FINISHED' ? 'not-allowed' : 'pointer',
            }}
          >
            {actionLoading ? 'Processing...' : 'Start Trivia'}
          </button>
          <button
            onClick={handleNextQuestion}
            disabled={actionLoading || activeTrivia?.status !== 'IN_PROGRESS'}
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: actionLoading || activeTrivia?.status !== 'IN_PROGRESS' ? '#ccc' : '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: actionLoading || activeTrivia?.status !== 'IN_PROGRESS' ? 'not-allowed' : 'pointer',
            }}
          >
            {actionLoading ? 'Processing...' : 'Next Question'}
          </button>
        </div>
      )}

      {currentQuestion && (
        <div style={{ marginBottom: '2rem', padding: '1rem', backgroundColor: '#fff', borderRadius: '4px', border: '1px solid #ddd' }}>
          <h3>Current Question</h3>
          <p>
            <strong>Question {currentQuestion.current_question_index + 1} of {currentQuestion.total_questions}</strong>
          </p>
          <p style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>{currentQuestion.question_text}</p>
          <ul style={{ listStyle: 'none', padding: 0 }}>
            {currentQuestion.options.map((option) => (
              <li key={option.id} style={{ padding: '0.5rem', marginBottom: '0.5rem', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
                {option.text}
              </li>
            ))}
          </ul>
          {currentQuestion.time_remaining_seconds !== undefined && (
            <p style={{ marginTop: '1rem', color: '#666' }}>
              Time remaining: {currentQuestion.time_remaining_seconds}s
            </p>
          )}
        </div>
      )}

      <div>
        <h3>Live Ranking</h3>
        {!activeTriviaId ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>Select a trivia to see ranking</div>
        ) : ranking && ranking.entries.length > 0 ? (
          <div style={{ backgroundColor: '#fff', borderRadius: '4px', border: '1px solid #ddd', overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#f5f5f5' }}>
                  <th style={{ padding: '0.75rem', textAlign: 'left', borderBottom: '1px solid #ddd' }}>Position</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', borderBottom: '1px solid #ddd' }}>Player</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', borderBottom: '1px solid #ddd' }}>Score</th>
                </tr>
              </thead>
              <tbody>
                {ranking.entries.map((entry) => (
                  <tr key={entry.user_id} style={{ borderBottom: '1px solid #eee' }}>
                    <td style={{ padding: '0.75rem' }}>{entry.position}</td>
                    <td style={{ padding: '0.75rem' }}>{entry.user_name}</td>
                    <td style={{ padding: '0.75rem' }}>{entry.score}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>No ranking data available</div>
        )}
      </div>
    </div>
  );
}
