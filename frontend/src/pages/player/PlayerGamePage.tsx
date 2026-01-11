import { useEffect, useState, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { getStatus, getCurrentQuestion, submitAnswer, updateHeartbeat, useFiftyFiftyLifeline } from '../../api/player';
import { usePolling } from '../../hooks/usePolling';
import type { TriviaStatusDTO, CurrentQuestionDTO, SubmitAnswerDTO } from '../../types/player';

type QuestionUIState = 'IDLE' | 'ACTIVE' | 'ANSWERED' | 'TIMEOUT' | 'WAITING_NEXT';

export default function PlayerGamePage() {
  const { triviaId } = useParams<{ triviaId: string }>();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [uiState, setUiState] = useState<QuestionUIState>('IDLE');
  const [selectedOptionId, setSelectedOptionId] = useState<string | null>(null);
  const [answerLocked, setAnswerLocked] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState<number>(0);
  const [fiftyFiftyUsed, setFiftyFiftyUsed] = useState(false);
  const [usingFiftyFifty, setUsingFiftyFifty] = useState(false);
  const [allowedOptions, setAllowedOptions] = useState<string[] | null>(null);

  // Refs to avoid re-renders on polling
  const lastQuestionIdRef = useRef<string | null>(null);
  const selectedOptionIdRef = useRef<string | null>(null);
  const answerLockedRef = useRef(false);
  const uiStateRef = useRef<QuestionUIState>('IDLE');

  // Poll status and navigate if needed
  const { data: statusData } = usePolling<TriviaStatusDTO>(
    async () => {
      if (!triviaId) throw new Error('No trivia ID');
      const response = await getStatus(triviaId);
      if (response.error) throw new Error(response.error);
      if (!response.data) throw new Error('No status data');
      return response.data;
    },
    {
      intervalMs: 1000,
      enabled: !!triviaId,
      onData: (data) => {
        if (data.state === 'WAITING') {
          navigate(`/play/trivias/${triviaId}/lobby`);
        } else if (data.state === 'FINISHED') {
          navigate(`/play/trivias/${triviaId}/results`);
        }
      },
    }
  );

  // Poll current question
  const {
    data: questionData,
    error: questionError,
    loading: questionLoading,
  } = usePolling<CurrentQuestionDTO>(
    async () => {
      if (!triviaId || !user) throw new Error('No trivia ID or user');
      const response = await getCurrentQuestion(triviaId, user.id);
      if (response.error) throw new Error(response.error);
      if (!response.data) throw new Error('No question data');
      return response.data;
    },
    {
      intervalMs: 2000,
      enabled: !!triviaId && !!user && statusData?.state === 'IN_PROGRESS',
    }
  );
        
  // Reset state only when question_id changes
  useEffect(() => {
    if (!questionData) return;

    const currentQuestionId = questionData.question_id;
    const previousQuestionId = lastQuestionIdRef.current;

    if (previousQuestionId !== currentQuestionId) {
      lastQuestionIdRef.current = currentQuestionId;
      const newTimeRemaining = Math.max(0, questionData.remaining_seconds);

      setTimeRemaining(newTimeRemaining);
      setSelectedOptionId(null);
      selectedOptionIdRef.current = null;
      setAnswerLocked(false);
      answerLockedRef.current = false;
      setSubmitting(false);
      setAllowedOptions(null); // Reset allowed options for new question
      setFiftyFiftyUsed(!questionData.fifty_fifty_available); // Update based on availability

      if (newTimeRemaining > 0) {
        setUiState('ACTIVE');
        uiStateRef.current = 'ACTIVE';
      } else {
        setUiState('TIMEOUT');
        uiStateRef.current = 'TIMEOUT';
      }
    }
  }, [questionData?.question_id]);

  // Update time from backend without resetting local UI state
  useEffect(() => {
    if (!questionData) return;

    const currentQuestionId = questionData.question_id;
    if (lastQuestionIdRef.current !== currentQuestionId) {
      return; // Different question: let reset effect handle
    }

    if (!answerLockedRef.current) {
      const newTimeRemaining = Math.max(0, questionData.remaining_seconds);
      setTimeRemaining(newTimeRemaining);

      // Do not touch uiState if user already picked an option
      if (!selectedOptionIdRef.current) {
        if (newTimeRemaining <= 0 && uiStateRef.current === 'ACTIVE') {
          setUiState('TIMEOUT');
          uiStateRef.current = 'TIMEOUT';
        } else if (newTimeRemaining <= 0 && uiStateRef.current === 'TIMEOUT' && statusData?.state === 'IN_PROGRESS') {
          setUiState('WAITING_NEXT');
          uiStateRef.current = 'WAITING_NEXT';
        }
      }
    }
  }, [questionData?.remaining_seconds, statusData?.state]);

  // Keep refs in sync with state
  useEffect(() => {
    selectedOptionIdRef.current = selectedOptionId;
  }, [selectedOptionId]);
  useEffect(() => {
    answerLockedRef.current = answerLocked;
  }, [answerLocked]);
  useEffect(() => {
    uiStateRef.current = uiState;
  }, [uiState]);

  // Local countdown (for UX only)
  useEffect(() => {
    if (timeRemaining <= 0 || answerLocked) {
      if (timeRemaining <= 0 && !answerLocked && uiState === 'ACTIVE' && !selectedOptionId) {
        setUiState('TIMEOUT');
        uiStateRef.current = 'TIMEOUT';
      }
      return;
    }

    const timer = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 1) {
          if (!answerLocked && !selectedOptionId) {
            setUiState('TIMEOUT');
            uiStateRef.current = 'TIMEOUT';
          }
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [timeRemaining, answerLocked, uiState, selectedOptionId]);

  const handleOptionSelect = (optionId: string) => {
    if (answerLocked || submitting || timeRemaining <= 0 || uiState !== 'ACTIVE') {
      return;
    }
    selectedOptionIdRef.current = optionId; // sync ref immediately
    setSelectedOptionId(optionId);
  };

  // Update fiftyFiftyUsed when questionData changes
  useEffect(() => {
    if (questionData) {
      setFiftyFiftyUsed(!questionData.fifty_fifty_available);
    }
  }, [questionData?.fifty_fifty_available]);

  const handleUseFiftyFifty = async () => {
    if (!triviaId || !user || !questionData || fiftyFiftyUsed || usingFiftyFifty || answerLocked) {
      return;
    }

    setUsingFiftyFifty(true);

    try {
      const response = await useFiftyFiftyLifeline(triviaId, questionData.question_id, user.id);

      if (response.error) {
        alert(`Error usando comodín 50/50: ${response.error}`);
        setUsingFiftyFifty(false);
        return;
      }

      if (response.data) {
        // Update allowed options
        const allowedIds = response.data.allowed_options.map((opt) => opt.id);
        setAllowedOptions(allowedIds);
        setFiftyFiftyUsed(true);
      }
    } catch (err) {
      alert(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setUsingFiftyFifty(false);
    }
  };

  const handleSubmit = async () => {
    if (answerLocked || submitting || !triviaId || !user || !selectedOptionId || !questionData) {
      return;
    }

    setAnswerLocked(true);
    answerLockedRef.current = true;
    setSubmitting(true);

    try {
      const payload: SubmitAnswerDTO = {
        question_id: questionData.question_id,
        option_id: selectedOptionId,
      };

      const response = await submitAnswer(triviaId, user.id, payload);

      if (response.error) {
        if (response.error.includes('already') || response.error.includes('409')) {
          setUiState('ANSWERED');
          uiStateRef.current = 'ANSWERED';
        } else {
          setAnswerLocked(false);
          answerLockedRef.current = false;
          setSubmitting(false);
          alert(`Error submitting answer: ${response.error}`);
        }
      } else if (response.data?.accepted || response.data?.already_answered) {
        setUiState('ANSWERED');
        uiStateRef.current = 'ANSWERED';
      } else {
        setAnswerLocked(false);
        answerLockedRef.current = false;
        setSubmitting(false);
      }
    } catch (err) {
      setAnswerLocked(false);
      answerLockedRef.current = false;
      setSubmitting(false);
      alert(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setSubmitting(false);
    }
  };

  // Heartbeat
  const heartbeatIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  useEffect(() => {
    if (!triviaId || !user) return;

    const sendHeartbeat = async () => {
      try {
        await updateHeartbeat(triviaId, user.id);
      } catch (error) {
        console.warn('Heartbeat failed:', error);
      }
    };

    sendHeartbeat();
    heartbeatIntervalRef.current = setInterval(sendHeartbeat, 5000);

    return () => {
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
        heartbeatIntervalRef.current = null;
      }
    };
  }, [triviaId, user]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (statusData?.state !== 'IN_PROGRESS') {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <h1>Waiting for game to start...</h1>
        <p>Redirecting...</p>
      </div>
    );
  }

  return (
    <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1>Game</h1>
        <button
          onClick={handleLogout}
          style={{
            padding: '0.75rem 1.5rem',
            backgroundColor: '#dc3545',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          Logout
        </button>
      </div>

      {questionError !== undefined && (
        <div style={{ padding: '0.75rem', backgroundColor: '#fff3cd', color: '#856404', borderRadius: '4px', marginBottom: '1rem' }}>
          Error loading question: {questionError instanceof Error 
            ? questionError.message 
            : typeof questionError === 'string' 
              ? questionError 
              : 'Unknown error'}
        </div>
      )}

      {questionLoading && !questionData ? (
        <div style={{ textAlign: 'center', padding: '2rem' }}>Loading question...</div>
      ) : questionData ? (
        <div>
          {/* Progress */}
          <div style={{ marginBottom: '2rem', textAlign: 'center' }}>
            <h2>
              Pregunta {questionData.question_index + 1} de {questionData.total_questions || '?'}
            </h2>
            <div
              style={{
                width: '100%',
                height: '8px',
                backgroundColor: '#e9ecef',
                borderRadius: '4px',
                marginTop: '0.5rem',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  width: `${((questionData.question_index + 1) / (questionData.total_questions || 1)) * 100}%`,
                  height: '100%',
                  backgroundColor: '#007bff',
                  transition: 'width 0.3s ease',
                }}
              />
            </div>
          </div>

          {/* Countdown */}
          <div
            style={{
              textAlign: 'center',
              marginBottom: '2rem',
              fontSize: '3rem',
              fontWeight: 'bold',
              color: timeRemaining <= 5 ? '#dc3545' : timeRemaining <= 10 ? '#ffc107' : '#28a745',
            }}
          >
            {Math.max(0, timeRemaining)}s
          </div>

          {/* Question */}
          <div style={{ backgroundColor: '#fff', borderRadius: '4px', border: '1px solid #ddd', padding: '1.5rem', marginBottom: '2rem' }}>
            <h2 style={{ marginTop: 0 }}>{questionData.text}</h2>
          </div>

          {/* Status Messages */}
          {uiState === 'ANSWERED' && (
            <div
              style={{
                padding: '1rem',
                backgroundColor: '#d4edda',
                color: '#155724',
                borderRadius: '4px',
                textAlign: 'center',
                fontWeight: 'bold',
                marginBottom: '1rem',
              }}
            >
              ✅ Respuesta enviada
            </div>
          )}

          {uiState === 'TIMEOUT' && (
            <div
              style={{
                padding: '1rem',
                backgroundColor: '#f8d7da',
                color: '#721c24',
                borderRadius: '4px',
                textAlign: 'center',
                fontWeight: 'bold',
                marginBottom: '1rem',
              }}
            >
              ⏱️ Tiempo agotado
            </div>
          )}

          {uiState === 'WAITING_NEXT' && (
            <div
              style={{
                padding: '1rem',
                backgroundColor: '#fff3cd',
                color: '#856404',
                borderRadius: '4px',
                textAlign: 'center',
                fontWeight: 'bold',
                marginBottom: '1rem',
              }}
            >
              ⏳ Esperando la siguiente pregunta…
            </div>
          )}

          {/* 50/50 Lifeline Button */}
          {questionData.fifty_fifty_available && !fiftyFiftyUsed && (
            <div style={{ marginBottom: '1rem', textAlign: 'center' }}>
              <button
                onClick={handleUseFiftyFifty}
                disabled={usingFiftyFifty || answerLocked || timeRemaining <= 0 || uiState !== 'ACTIVE'}
                style={{
                  padding: '0.75rem 1.5rem',
                  fontSize: '1rem',
                  backgroundColor: usingFiftyFifty || answerLocked || timeRemaining <= 0 || uiState !== 'ACTIVE' ? '#ccc' : '#ff9800',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: usingFiftyFifty || answerLocked || timeRemaining <= 0 || uiState !== 'ACTIVE' ? 'not-allowed' : 'pointer',
                  fontWeight: 'bold',
                }}
              >
                {usingFiftyFifty ? 'Usando comodín...' : '🎯 Comodín 50/50'}
              </button>
            </div>
          )}

          {/* Options */}
          <div 
            key={questionData.question_id}
            style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '2rem' }}
          >
            {questionData.options
              .filter((option) => !allowedOptions || allowedOptions.includes(option.id))
              .map((option) => {
              const isSelected = selectedOptionId === option.id;
              const isDisabled = answerLocked || submitting || timeRemaining <= 0 || uiState !== 'ACTIVE';

              return (
                <button
                  key={option.id}
                  onClick={() => handleOptionSelect(option.id)}
                  disabled={isDisabled}
                  style={{
                    padding: '1rem',
                    fontSize: '1rem',
                    textAlign: 'left',
                    border: isSelected ? '3px solid #007bff' : '1px solid #ddd',
                    borderRadius: '4px',
                    backgroundColor: isSelected ? '#e7f3ff' : '#fff',
                    cursor: isDisabled ? 'not-allowed' : 'pointer',
                    opacity: isDisabled && !isSelected ? 0.5 : 1,
                    transition: 'all 0.2s ease',
                  }}
                >
                  {option.text}
                </button>
              );
            })}
          </div>

          {/* Submit button: always visible below options */}
          <div style={{ marginTop: '1rem' }}>
            <button
              onClick={handleSubmit}
              disabled={submitting || answerLocked}
              style={{
                width: '100%',
                padding: '1rem',
                fontSize: '1.1rem',
                // Estado base: blanco completo; cuando hay opción seleccionada y está listo, verde
                backgroundColor: selectedOptionId && !submitting && !answerLocked ? '#28a745' : '#ffffff',
                color: '#ffffff',
                border: selectedOptionId && !submitting && !answerLocked ? '2px solid #000' : '2px solid #ffffff',
                borderRadius: '4px',
                cursor: submitting || answerLocked ? 'not-allowed' : 'pointer',
                fontWeight: 'bold',
              }}
            >
              {submitting ? 'Enviando...' : 'Enviar Respuesta'}
            </button>
          </div>
        </div>
      ) : (
        <div style={{ textAlign: 'center', padding: '2rem' }}>No question available</div>
      )}
    </div>
  );
}
