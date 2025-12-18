import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getTriviaById } from '../../api/triviasApi';
import { Trivia } from '../../types';
import TriviaQuestionsTab from './trivia/TriviaQuestionsTab';
import TriviaPlayersTab from './trivia/TriviaPlayersTab';
import TriviaControlTab from './trivia/TriviaControlTab';

type Tab = 'overview' | 'players' | 'questions' | 'control';

export default function TriviaDetailPage() {
  const { triviaId } = useParams<{ triviaId: string }>();
  const navigate = useNavigate();
  const [trivia, setTrivia] = useState<Trivia | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<Tab>('overview');

  useEffect(() => {
    if (triviaId) {
      loadTrivia();
    }
  }, [triviaId]);

  const loadTrivia = async () => {
    if (!triviaId) return;
    setLoading(true);
    const response = await getTriviaById(triviaId);
    if (response.data) {
      setTrivia(response.data);
    }
    // If endpoint doesn't exist, we still allow the page to work with just the ID
    setLoading(false);
  };

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: 'overview', label: 'Resumen' },
    { id: 'players', label: 'Jugadores' },
    { id: 'questions', label: 'Preguntas' },
    { id: 'control', label: 'Control' },
  ];

  if (loading) {
    return <div className="text-center py-4">Cargando...</div>;
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <button
            onClick={() => navigate('/admin/trivias')}
            className="btn btn-secondary btn-sm mb-3 btn-animated"
          >
            ← Volver a Trivias
          </button>
          <h2 className="fw-bold mb-1">{trivia?.title || 'Detalle de Trivia'}</h2>
          {triviaId && (
            <p className="text-muted small mb-0">
              ID: {triviaId}
            </p>
          )}
        </div>
      </div>

      {trivia && (
        <div className="card mb-4 fade-in">
          <div className="card-body">
            <p className="mb-2">
              <strong>Estado:</strong> <span className="badge bg-light text-dark">{trivia.status}</span>
            </p>
            <p className="mb-2">
              <strong>Índice de pregunta actual:</strong> {trivia.current_question_index}
            </p>
            {trivia.description && (
              <p className="mb-2">
                <strong>Descripción:</strong> {trivia.description}
              </p>
            )}
            {trivia.started_at && (
              <p className="mb-0">
                <strong>Iniciada en:</strong> {new Date(trivia.started_at).toLocaleString('es-ES')}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-bottom mb-4">
        <div className="d-flex gap-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`btn btn-sm btn-animated ${
                activeTab === tab.id ? 'btn-primary' : 'btn-outline-secondary'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'overview' && (
          <div className="fade-in">
            <h4 className="mb-3">Resumen</h4>
            {trivia ? (
              <div className="card">
                <div className="card-body">
                  <p className="mb-2">
                    <strong>Título:</strong> {trivia.title}
                  </p>
                  <p className="mb-2">
                    <strong>Descripción:</strong> {trivia.description}
                  </p>
                  <p className="mb-2">
                    <strong>Estado:</strong> <span className="badge bg-light text-dark">{trivia.status}</span>
                  </p>
                  <p className="mb-2">
                    <strong>Índice de pregunta actual:</strong> {trivia.current_question_index}
                  </p>
                  {trivia.created_at && (
                    <p className="mb-0">
                      <strong>Creada en:</strong> {new Date(trivia.created_at).toLocaleString('es-ES')}
                    </p>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center text-muted py-4">
                Metadatos de trivia no disponibles. Usando ID de trivia: {triviaId}
              </div>
            )}
          </div>
        )}

        {activeTab === 'players' && triviaId && <TriviaPlayersTab triviaId={triviaId} />}

        {activeTab === 'questions' && triviaId && <TriviaQuestionsTab triviaId={triviaId} />}

        {activeTab === 'control' && triviaId && (
          <TriviaControlTab
            triviaId={triviaId}
            triviaStatus={trivia?.status}
            onStatusUpdate={loadTrivia}
          />
        )}
      </div>
    </div>
  );
}
