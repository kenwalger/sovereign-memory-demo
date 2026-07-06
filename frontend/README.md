# Sovereign Memory Demo — Frontend

React + TypeScript + Vite interface for the institutional memory demo.

## Requirements

- Node.js 20+
- npm (or compatible package manager)
- Backend API running on `http://localhost:8000`

## Setup

```bash
cd frontend
npm install
```

## Development

```bash
npm run dev
```

The Vite dev server proxies `/api` requests to the backend on port 8000.

## Build

```bash
npm run build
```

Production deployment target: `sovereignplatform.dev/demos/memory`

## Panels

| Component | Purpose |
|-----------|---------|
| `QuestionPanel` | Prompt input and query submission |
| `AnswerPanel` | Mock natural language answer |
| `EvidencePanel` | Raw evidence chunks and source attribution |
| `ReceiptPanel` | Forensic receipt JSON envelope |
