/**
 * HTTP client for the Sovereign Memory Demo backend API.
 *
 * @module services/api
 */

import type {
  QuestionRequest,
  QuestionResponse,
  ReceiptEnvelope,
} from "@/types/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

/**
 * Typed HTTP error raised when the backend returns a non-success status code.
 */
export class ApiError extends Error {
  /** HTTP status code returned by the backend. */
  readonly status: number;

  /**
   * Create a new API error instance.
   *
   * @param message - Human-readable error detail from the backend response.
   * @param status - HTTP status code associated with the failed request.
   */
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/**
 * Parse a fetch response or raise an {@link ApiError}.
 *
 * @typeParam T - Expected JSON response shape.
 * @param response - Raw fetch response from the backend.
 * @returns Parsed JSON payload when the response is successful.
 * @throws {ApiError} When the response status is not OK.
 */
async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) {
        detail = body.detail;
      }
    } catch {
      // Response body is not JSON; keep status text.
    }
    throw new ApiError(detail, response.status);
  }

  return (await response.json()) as T;
}

/**
 * Submit a question to the institutional memory API.
 *
 * Executes the full backend lifecycle: retrieval, answer assembly, source
 * attribution, and forensic receipt generation when evidence is found.
 *
 * @param question - Natural-language question to submit.
 * @returns Unified question lifecycle response from the backend.
 * @throws {ApiError} When request validation fails or the backend returns an error.
 */
export async function askQuestion(question: string): Promise<QuestionResponse> {
  const payload: QuestionRequest = { question };
  const response = await fetch(`${API_BASE}/api/questions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  return parseResponse<QuestionResponse>(response);
}

/**
 * Fetch a persisted forensic receipt by identifier.
 *
 * @param receiptId - Forensic receipt identifier (for example `FR-0001`).
 * @returns Parsed receipt envelope stored in the relational tier.
 * @throws {ApiError} When the receipt does not exist or the backend returns an error.
 */
export async function fetchReceipt(receiptId: string): Promise<ReceiptEnvelope> {
  const response = await fetch(
    `${API_BASE}/api/receipts/${encodeURIComponent(receiptId)}`,
  );

  return parseResponse<ReceiptEnvelope>(response);
}
