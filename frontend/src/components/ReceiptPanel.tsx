import { isSdkReceiptMetadata, type ReceiptEnvelope } from "@/types/api";

import "./Panel.css";
import "./ReceiptPanel.css";

/**
 * Props for the forensic receipt display panel.
 *
 * @property receipt - Tamper-evident receipt envelope returned by the backend.
 * @property loading - Whether the question lifecycle request is in flight.
 */
interface ReceiptPanelProps {
  receipt: ReceiptEnvelope | null;
  loading: boolean;
}

/**
 * Render the formatted forensic receipt JSON cryptographic tracking envelope.
 *
 * @param props - Receipt envelope and loading state.
 * @returns Receipt panel with summary metadata and full JSON payload.
 */
export function ReceiptPanel({ receipt, loading }: ReceiptPanelProps) {
  const sdkMetadata =
    receipt !== null && isSdkReceiptMetadata(receipt.metadata)
      ? receipt.metadata
      : null;

  return (
    <section className="panel receipt-panel">
      <header className="panel__header">Forensic Receipt</header>
      <div className="panel__body">
        {loading ? (
          <p className="panel__loading">Sealing forensic receipt envelope...</p>
        ) : receipt ? (
          <div className="receipt-view">
            <dl className="receipt-view__summary">
              <div>
                <dt>Receipt ID</dt>
                <dd>{receipt.receipt_id}</dd>
              </div>
              <div>
                <dt>Confidence</dt>
                <dd>{receipt.confidence.toFixed(2)}</dd>
              </div>
              <div>
                <dt>Ledger Reference</dt>
                <dd>{receipt.ledger_reference}</dd>
              </div>
              <div>
                <dt>Payload Hash</dt>
                <dd className="receipt-view__hash">{receipt.metadata.payload_hash}</dd>
              </div>
              {sdkMetadata !== null && (
                <>
                  <div>
                    <dt>Prose Tax Savings</dt>
                    <dd className="receipt-view__metric--teal">
                      {sdkMetadata.tax_savings_percentage.toFixed(1)}%
                    </dd>
                  </div>
                  <div>
                    <dt>Token Reduction</dt>
                    <dd className="receipt-view__metric--teal">
                      {sdkMetadata.raw_tokens} → {sdkMetadata.sieved_tokens}
                    </dd>
                  </div>
                </>
              )}
            </dl>
            <pre className="code-frame receipt-view__json">
              {JSON.stringify(receipt, null, 2)}
            </pre>
          </div>
        ) : (
          <p className="panel__empty">
            A forensic receipt will appear here after a successful question lifecycle.
          </p>
        )}
      </div>
    </section>
  );
}
