import React from "react";
import { createRoot } from "react-dom/client";
import ComplaintTracker from "./components/ComplaintTracker.jsx";
import "./styles.css";

const mount = document.getElementById("reactComplaintTracker");

if (mount) {
  createRoot(mount).render(
    <React.StrictMode>
      <ComplaintTracker initialEmail={mount.dataset.email || ""} />
    </React.StrictMode>,
  );
}
