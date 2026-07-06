import { useState, type FormEvent } from "react";

import "./Panel.css";

/**
 * Props for the question input panel.
 *
 * @property loading - Whether a question lifecycle request is in flight.
 * @property onSubmit - Callback invoked with a trimmed question string.
 */
interface QuestionPanelProps {
  loading: boolean;
  onSubmit: (question: string) => void;
}

/**
 * Capture user questions and trigger the institutional memory query lifecycle.
 *
 * @param props - Panel state and submission callback.
 * @returns Question input form and submission controls.
 */
export function QuestionPanel({ loading, onSubmit }: QuestionPanelProps) {
  const [question, setQuestion] = useState("Who is Fido?");

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || loading) {
      return;
    }
    onSubmit(trimmed);
  };

  return (
    <section className="panel question-panel">
      <header className="panel__header">Question</header>
      <div className="panel__body">
        <form className="question-form" onSubmit={handleSubmit}>
          <label className="question-form__label" htmlFor="question-input">
            Ask the institutional memory corpus
          </label>
          <textarea
            id="question-input"
            className="question-form__input"
            rows={3}
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Who is Fido?"
            disabled={loading}
          />
          <button className="question-form__button" type="submit" disabled={loading}>
            {loading ? "Retrieving memory..." : "Ask Question"}
          </button>
        </form>
      </div>
    </section>
  );
}
