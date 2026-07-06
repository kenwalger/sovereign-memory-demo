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
 * Shared forensic metadata fields present on every receipt envelope.
 *
 * @property payload_hash - Deterministic pre-sieve SHA-256 digest of evidence strings.
 * @property ledger_reference - Ledger linkage reference derived from the payload hash.
 * @property airlock_boundary - Outbound governance boundary label for airlock integration.
 */
export interface ReceiptMetadataBase {
  payload_hash: string;
  ledger_reference: string;
  airlock_boundary: string;
}

/**
 * Offline simulated seal metadata emitted without a live SDK ledger commit.
 *
 * @property signature - Tamper-evident signature for audit replay.
 * @property seal_algorithm - Algorithm identifier used by the seal simulation.
 */
export interface SimulatedSealMetadata extends ReceiptMetadataBase {
  signature: string;
  seal_algorithm: string;
}

/**
 * Live SDK telemetry metadata emitted by sieve and airlock processing.
 *
 * @property raw_tokens - Token count of the unified outbound context before sieve.
 * @property sieved_tokens - Token count after context minimisation.
 * @property tax_savings_percentage - Prose Tax savings percentage from the sieve pass.
 * @property policy_warnings - Non-blocking airlock policy warnings, if any.
 * @property signature - Optional Ed25519 signature from the SDK forensic receipt.
 * @property public_key - Optional public key associated with the SDK signature.
 * @property sdk_timestamp - Optional ISO timestamp from the SDK receipt envelope.
 * @property sdk_metadata - Optional nested SDK receipt metadata payload.
 */
export interface SdkReceiptMetadata extends ReceiptMetadataBase {
  raw_tokens: number;
  sieved_tokens: number;
  tax_savings_percentage: number;
  policy_warnings: string[];
  signature?: string;
  public_key?: string;
  sdk_timestamp?: string;
  sdk_metadata?: Record<string, unknown>;
}

/**
 * Forensic seal metadata union covering simulated and live SDK receipt envelopes.
 */
export type ReceiptMetadata = SimulatedSealMetadata | SdkReceiptMetadata;

/**
 * Type guard identifying live SDK telemetry receipt metadata.
 *
 * @param metadata - Receipt metadata payload from the backend.
 * @returns `true` when the metadata includes sieve telemetry fields.
 */
export function isSdkReceiptMetadata(
  metadata: ReceiptMetadata,
): metadata is SdkReceiptMetadata {
  return "raw_tokens" in metadata;
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
