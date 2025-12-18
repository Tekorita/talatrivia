import { useState, useEffect, FormEvent } from 'react';
import { getQuestions, createQuestion } from '../../api/questionsApi';
import { Question } from '../../types';

interface QuestionOption {
  text: string;
  is_correct: boolean;
}

export default function QuestionsPage() {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  // Form state
  const [text, setText] = useState('');
  const [difficulty, setDifficulty] = useState<'EASY' | 'MEDIUM' | 'HARD'>('EASY');
  const [options, setOptions] = useState<QuestionOption[]>([
    { text: '', is_correct: false },
    { text: '', is_correct: false },
    { text: '', is_correct: false },
    { text: '', is_correct: false },
  ]);

  useEffect(() => {
    loadQuestions();
  }, []);

  const loadQuestions = async () => {
    setLoading(true);
    setError(null);
    const response = await getQuestions();
    if (response.error) {
      if (response.error.includes('404') || response.error.includes('not found')) {
        setError('El endpoint aún no está disponible');
      } else {
        setError(response.error);
      }
    } else if (response.data) {
      setQuestions(response.data);
    }
    setLoading(false);
  };

  const handleOptionChange = (index: number, value: string) => {
    const newOptions = [...options];
    newOptions[index].text = value;
    setOptions(newOptions);
  };

  const handleCorrectOptionChange = (index: number) => {
    const newOptions = options.map((opt, i) => ({
      ...opt,
      is_correct: i === index,
    }));
    setOptions(newOptions);
  };

  const canSubmit = () => {
    const hasText = text.trim().length > 0;
    const allOptionsFilled = options.every((opt) => opt.text.trim().length > 0);
    const hasOneCorrect = options.filter((opt) => opt.is_correct).length === 1;
    return hasText && allOptionsFilled && hasOneCorrect;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!canSubmit()) {
      setCreateError('Por favor completa todos los campos y selecciona exactamente una opción correcta');
      return;
    }

    setCreateLoading(true);
    setCreateError(null);

    const response = await createQuestion({
      text: text.trim(),
      difficulty,
      options: options.map((opt) => ({
        text: opt.text.trim(),
        is_correct: opt.is_correct,
      })),
    });

    if (response.error) {
      if (response.error.includes('404') || response.error.includes('not found')) {
        setCreateError('El endpoint aún no está disponible');
      } else {
        setCreateError(response.error);
      }
    } else if (response.data) {
      // Reset form
      setText('');
      setDifficulty('EASY');
      setOptions([
        { text: '', is_correct: false },
        { text: '', is_correct: false },
        { text: '', is_correct: false },
        { text: '', is_correct: false },
      ]);
      setShowForm(false);
      // Reload questions
      loadQuestions();
    }
    setCreateLoading(false);
  };

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h2 className="fw-bold mb-1">Preguntas</h2>
          <p className="text-muted mb-0">Administra las preguntas del sistema.</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="btn btn-primary btn-animated"
        >
          {showForm ? 'Cancelar' : 'Crear pregunta'}
        </button>
      </div>

      {showForm && (
        <div className="card mb-4 fade-in">
          <div className="card-body">
            <h5 className="card-title mb-3">Crear pregunta</h5>
            {createError && (
              <div className="alert alert-danger">{createError}</div>
            )}
            <form onSubmit={handleSubmit} className="row g-3">
              <div className="col-12">
                <label className="form-label">Texto de la pregunta *</label>
                <textarea
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  required
                  disabled={createLoading}
                  rows={3}
                  className="form-control"
                  placeholder="Escribe la pregunta aquí..."
                />
              </div>
              <div className="col-12">
                <label className="form-label">Dificultad *</label>
                <select
                  value={difficulty}
                  onChange={(e) => setDifficulty(e.target.value as 'EASY' | 'MEDIUM' | 'HARD')}
                  disabled={createLoading}
                  className="form-select"
                >
                  <option value="EASY">Fácil</option>
                  <option value="MEDIUM">Medio</option>
                  <option value="HARD">Difícil</option>
                </select>
              </div>
              <div className="col-12">
                <label className="form-label">Opciones * (Selecciona exactamente una como correcta)</label>
                {options.map((option, index) => (
                  <div key={index} className="d-flex align-items-center gap-2 mb-2">
                    <input
                      type="radio"
                      name="correct_option"
                      checked={option.is_correct}
                      onChange={() => handleCorrectOptionChange(index)}
                      disabled={createLoading}
                      className="form-check-input"
                    />
                    <input
                      type="text"
                      value={option.text}
                      onChange={(e) => handleOptionChange(index, e.target.value)}
                      placeholder={`Opción ${index + 1}`}
                      required
                      disabled={createLoading}
                      className="form-control"
                    />
                  </div>
                ))}
              </div>
              <div className="col-12 d-flex justify-content-end">
                <button
                  type="submit"
                  disabled={createLoading || !canSubmit()}
                  className="btn btn-success btn-animated"
                >
                  {createLoading ? 'Creando...' : 'Crear pregunta'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {error && (
        <div className="alert alert-warning">{error}</div>
      )}

      {loading ? (
        <div className="text-center py-4">Cargando...</div>
      ) : questions.length === 0 && !error ? (
        <div className="text-center text-muted py-5">No hay preguntas creadas</div>
      ) : (
        <div className="card fade-in">
          <div className="table-responsive">
            <table className="table align-middle mb-0">
              <thead>
                <tr>
                  <th>Texto</th>
                  <th>Dificultad</th>
                </tr>
              </thead>
              <tbody>
                {questions.map((question) => (
                  <tr key={question.id}>
                    <td>{question.text}</td>
                    <td>
                      <span className="badge bg-light text-dark">
                        {question.difficulty === 'EASY' ? 'Fácil' : question.difficulty === 'MEDIUM' ? 'Medio' : 'Difícil'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
