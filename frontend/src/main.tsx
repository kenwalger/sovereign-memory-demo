/**
 * Application entrypoint for the Sovereign Memory Demo frontend.
 *
 * Mounts the {@link Home} page into the root DOM element.
 */

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { Home } from "@/pages/Home";

import "./index.css";

const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error("Root element not found");
}

createRoot(rootElement).render(
  <StrictMode>
    <Home />
  </StrictMode>,
);
