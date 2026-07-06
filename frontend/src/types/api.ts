/**
 * TypeScript contracts mirroring the Sovereign Memory Demo FastAPI schemas.
 *
 * @module types/api
 */

/**
 * Inbound question payload for `POST /api/questions`.
 *
 * @property question - Natural-language question submitted by the user.
 */
export interface QuestionRequest {
  question: string;
}

/**
 * Provenance mapping from a retrieved record to its upstream source document.
 *
 * @property record_id - Stable identifier of the matched memory record.
 * @property record_title - Human-readable title of the matched record.
 * @property record_classification - Domain classification assigned at ingestion.
 * @property record_confidence - Confidence score assigned to the matched record.
 * @property document_id - Foreign key to the parent source document.
 * @property document_filename - Original filename from the datasets directory.
 * @property document_type - Ingested document type (`json`, `markdown`, or `text`).
 */
export interface SourceAttribution {
  record_id: string;
  record_title: string;
  record_classification: string;
  record_confidence: number;
  document_id: string;
  document_filename: string;
  document_type: string;
}

/**
 * Forensic seal metadata embedded inside a receipt envelope.
 *
 * @property payload_hash - Deterministic pre-sieve SHA-256 digest of evidence strings.
 * @property signature - Simulated tamper-evident signature for audit replay.
 * @property seal_algorithm - Algorithm identifier used by the seal simulation.
 * @property ledger_reference - Ledger linkage reference derived from the payload hash.
 * @property airlock_boundary - Outbound governance boundary label for airlock integration.
 */
export interface ReceiptMetadata {
  payload_hash: string;
  signature: string;
  seal_algorithm: string;
  ledger_reference: string;
  airlock_boundary: string;
}

/**
 * Tamper-evident forensic receipt tracking envelope returned by the backend.
 *
 * @property receipt_id - Sequential forensic receipt identifier (for example `FR-0001`).
 * @property timestamp - ISO-8601 creation timestamp for the receipt envelope.
 * @property confidence - Aggregated confidence score for the matched evidence set.
 * @property sources - Upstream source filenames included in the receipt.
 * @property evidence - Raw contextual evidence strings sealed into the receipt.
 * @property ledger_reference - Ledger linkage reference for immutable audit replay.
 * @property metadata - Cryptographic seal metadata including the payload hash.
 */
export interface ReceiptEnvelope {
  receipt_id: string;
  timestamp: string;
  confidence: number;
  sources: string[];
  evidence: string[];
  ledger_reference: string;
  metadata: ReceiptMetadata;
}

/**
 * Unified question lifecycle response returned by `POST /api/questions`.
 *
 * @property answer - Mock natural-language answer assembled from matched evidence.
 * @property evidence - Raw contextual string chunks extracted from SQLite records.
 * @property sources - Structured provenance attributions for each matched record.
 * @property receipt - Forensic receipt envelope, or `null` when no evidence matched.
 */
export interface QuestionResponse {
  answer: string;
  evidence: string[];
  sources: SourceAttribution[];
  receipt: ReceiptEnvelope | null;
}
