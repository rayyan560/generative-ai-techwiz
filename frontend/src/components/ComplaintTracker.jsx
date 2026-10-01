import { useEffect, useState } from "react";

export default function ComplaintTracker({ initialEmail }) {
  const [ticketId, setTicketId] = useState("");
  const [email, setEmail] = useState(initialEmail);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function lookup(id, emailAddress) {
    const cleanId = (id || "").trim();
    const cleanEmail = (emailAddress || "").trim();
    if (!cleanId || !cleanEmail) {
      setError("Enter the ticket reference and the email used for the complaint.");
      return;
    }
    setError("");
    setResult(null);
    setLoading(true);
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 15000);
    try {
      const path = `/api/complaints/track/${encodeURIComponent(cleanId)}?email=${encodeURIComponent(cleanEmail)}`;
      const response = await fetch(path, { signal: controller.signal });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "We could not verify that ticket and email.");
      setResult(data);
    } catch (requestError) {
      setError(requestError.name === "AbortError" ? "The request timed out. Please try again." : requestError.message || "Tracking is temporarily unavailable.");
    } finally {
      window.clearTimeout(timeout);
      setLoading(false);
    }
  }

  useEffect(() => {
    window.supportNovaTrackTicket = (id, knownEmail = "") => {
      setTicketId(id || "");
      const emailToUse = knownEmail || email;
      if (knownEmail) setEmail(knownEmail);
      lookup(id, emailToUse);
      document.getElementById("trackSection")?.scrollIntoView({ behavior: "smooth", block: "start" });
    };
    return () => delete window.supportNovaTrackTicket;
  }, [email]);

  async function handleSubmit(event) {
    event.preventDefault();
    await lookup(ticketId, email);
  }

  return (
    <div className="sn-tracker">
      <form className="sn-tracker-form" onSubmit={handleSubmit}>
        <label>
          <span>Ticket reference</span>
          <input autoComplete="off" value={ticketId} onChange={(event) => setTicketId(event.target.value)} placeholder="CMP-00001" required />
        </label>
        <label>
          <span>Complaint email</span>
          <input type="email" autoComplete="email" maxLength={254} value={email} onChange={(event) => setEmail(event.target.value)} placeholder="Email used when submitting" required />
        </label>
        <button type="submit" disabled={loading}>
          <i className={loading ? "fa-solid fa-spinner fa-spin" : "fa-solid fa-magnifying-glass"} aria-hidden="true" />
          {loading ? "Checking…" : "Verify & track"}
        </button>
      </form>
      <p className="sn-tracker-privacy">We check the email against the ticket before showing its status.</p>
      <div className="sn-tracker-feedback" role="status" aria-live="polite">{error}</div>
      {result && (
        <article className="sn-tracker-result" aria-label="Complaint status">
          <header>
            <div>
              <h2>{result.complaint_title}</h2>
              <p>{result.complaint_id} · {result.product_or_service || "Product not specified"}</p>
            </div>
            <span className={`sn-tracker-status ${result.status === "Resolved" ? "is-resolved" : ""}`}>{result.status}</span>
          </header>
          <dl>
            <div><dt>Received</dt><dd>{result.submitted_at || "Not available"}</dd></div>
            <div><dt>Review team</dt><dd>{result.assigned_department || "Support team"}</dd></div>
          </dl>
          <p className="sn-tracker-update">{result.official_update}</p>
        </article>
      )}
    </div>
  );
}
