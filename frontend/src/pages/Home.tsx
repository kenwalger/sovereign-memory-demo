import { useCallback, useState } from "react";

import { AnswerPanel } from "@/components/AnswerPanel";
import { EvidencePanel } from "@/components/EvidencePanel";
import { QuestionPanel } from "@/components/QuestionPanel";
import { ReceiptPanel } from "@/components/ReceiptPanel";
import { ApiError, askQuestion } from "@/services/api";
import type { QuestionResponse } from "@/types/api";

import "./Home.css";

/**
 * Primary application page mounting the four institutional memory panels.
 *
 * Orchestrates question submission, loading state, graceful API error handling,
 * and empty-state rendering across the quad-panel workspace.
 *
 * @returns Home layout containing Question, Answer, Evidence, and Receipt panels.
 */
export function Home() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<QuestionResponse | null>(null);

  /**
   * Submit a question to the backend and populate panel state from the response.
   *
   * @param question - Trimmed natural-language question from the question panel.
   */
  const handleAskQuestion = useCallback(async (question: string) => {
    setLoading(true);
    setError(null);

    try {
      const result = await askQuestion(question);
      setResponse(result);
    } catch (caught) {
      const message =
        caught instanceof ApiError
          ? caught.message
          : "Unable to reach the institutional memory API.";
      setError(message);
      setResponse(null);
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <main className="home">
      <header className="home__hero">
        <h1 className="sovereign-heading-1">
          Sovereign Systems Specification Memory Demo
        </h1>
        <p className="home__lede sovereign-subtitle">
          Information without Provenance is Just Gossip.
        </p>
      </header>

      {error && <div className="panel__error">{error}</div>}

      <div className="home__grid">
        <QuestionPanel loading={loading} onSubmit={handleAskQuestion} />
        <AnswerPanel answer={response?.answer ?? null} loading={loading} />
        <EvidencePanel
          evidence={response?.evidence ?? []}
          sources={response?.sources ?? []}
          loading={loading}
        />
        <ReceiptPanel receipt={response?.receipt ?? null} loading={loading} />
      </div>
    </main>
  );
}
