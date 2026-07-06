import type { SourceAttribution } from "@/types/api";

import "./Panel.css";

/**
 * Props for the evidence display panel.
 *
 * @property evidence - Raw contextual evidence strings from SQLite records.
 * @property sources - Structured provenance attributions for matched records.
 * @property loading - Whether the question lifecycle request is in flight.
 */
interface EvidencePanelProps {
  evidence: string[];
  sources: SourceAttribution[];
  loading: boolean;
}

/**
 * Render raw evidence chunks and upstream source attribution metadata.
 *
 * @param props - Evidence strings, source attributions, and loading state.
 * @returns Evidence panel with empty and loading states.
 */
export function EvidencePanel({ evidence, sources, loading }: EvidencePanelProps) {
  const hasEvidence = evidence.length > 0;
  const hasSources = sources.length > 0;

  return (
    <section className="panel evidence-panel">
      <header className="panel__header">Evidence</header>
      <div className="panel__body">
        {loading ? (
          <p className="panel__loading">Retrieving contextual evidence chunks...</p>
        ) : !hasEvidence && !hasSources ? (
          <p className="panel__empty">
            No evidence matched this question. Retrieval without provenance is incomplete.
          </p>
        ) : (
          <>
            {hasEvidence && (
              <div className="evidence-block">
                <h3 className="evidence-block__title">Context Chunks</h3>
                <ul className="evidence-list">
                  {evidence.map((chunk, index) => (
                    <li key={`${index}-${chunk.slice(0, 24)}`}>
                      <pre className="evidence-list__chunk">{chunk}</pre>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {hasSources && (
              <div className="evidence-block">
                <h3 className="evidence-block__title">Source Attribution</h3>
                <ul className="source-list">
                  {sources.map((source) => (
                    <li key={source.record_id} className="source-list__item">
                      <strong>{source.document_filename}</strong>
                      <span>{source.record_title}</span>
                      <span>
                        {source.record_classification} · confidence{" "}
                        {source.record_confidence.toFixed(2)}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}
      </div>
    </section>
  );
}
