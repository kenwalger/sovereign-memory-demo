import "./Panel.css";

/**
 * Props for the answer display panel.
 *
 * @property answer - Natural-language answer returned by the backend.
 * @property loading - Whether the question lifecycle request is in flight.
 */
interface AnswerPanelProps {
  answer: string | null;
  loading: boolean;
}

/**
 * Display the mock natural-language answer returned by the backend.
 *
 * @param props - Answer text and loading state.
 * @returns Answer panel with empty and loading states.
 */
export function AnswerPanel({ answer, loading }: AnswerPanelProps) {
  return (
    <section className="panel answer-panel">
      <header className="panel__header">Answer</header>
      <div className="panel__body">
        {loading ? (
          <p className="panel__loading">Assembling answer from retrieved evidence...</p>
        ) : answer ? (
          <p>{answer}</p>
        ) : (
          <p className="panel__empty">
            Submit a question to generate an auditable institutional memory answer.
          </p>
        )}
      </div>
    </section>
  );
}
