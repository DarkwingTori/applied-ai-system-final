import { useState, useRef, useEffect, FormEvent } from "react";
import { AdvisorMessage } from "../components/AdvisorMessage";
import { api } from "../api/client";
import type { ChatMessage } from "../types";

const SUGGESTIONS = [
  "How often should I walk my Labrador?",
  "What should I feed my senior cat?",
  "How do I give my dog a pill?",
  "What enrichment is best for indoor cats?",
  "How often should I groom a long-haired dog?",
];

function genId() {
  return Math.random().toString(36).slice(2);
}

export function Advisor() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Hi! I'm your PawPal+ AI Advisor. Ask me anything about pet care — walks, feeding, grooming, medication, or enrichment — and I'll give you advice grounded in trusted pet care guidelines.",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [petName, setPetName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const query = input.trim();
    if (!query || loading) return;

    setInput("");
    setError(null);

    const userMsg: ChatMessage = {
      id: genId(),
      role: "user",
      content: query,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await api.ask(query, petName || undefined);
      const assistantMsg: ChatMessage = {
        id: genId(),
        role: "assistant",
        content: res.answer,
        confidence: res.confidence,
        sources: res.sources,
        low_confidence: res.low_confidence,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  function useSuggestion(text: string) {
    setInput(text);
  }

  return (
    <div className="mx-auto flex h-[calc(100vh-57px)] max-w-3xl flex-col">
      {/* Header */}
      <div className="border-b border-pawpal-border bg-white px-4 py-3">
        <h1 className="text-base font-semibold text-pawpal-text">Pet Care Advisor</h1>
        <p className="text-xs text-pawpal-muted">
          Answers grounded in veterinary and pet care guidelines via RAG
        </p>
      </div>

      {/* Optional pet name context */}
      <div className="border-b border-pawpal-border bg-pawpal-bg px-4 py-2">
        <input
          type="text"
          placeholder="Pet name (optional — e.g. Max)"
          value={petName}
          onChange={(e) => setPetName(e.target.value)}
          className="w-full rounded-lg border border-pawpal-border bg-white px-3 py-1.5 text-sm text-pawpal-text placeholder:text-pawpal-muted focus:outline-none focus:ring-2 focus:ring-brand-300"
        />
      </div>

      {/* Message thread */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.map((msg) => (
          <AdvisorMessage key={msg.id} message={msg} />
        ))}

        {loading && (
          <div className="flex gap-3">
            <div className="h-8 w-8 rounded-full bg-brand-100 flex items-center justify-center text-lg select-none">
              🐾
            </div>
            <div className="rounded-2xl rounded-tl-sm bg-white px-4 py-3 shadow-card border border-pawpal-border">
              <div className="flex gap-1.5 items-center h-5">
                {[0, 1, 2].map((i) => (
                  <span
                    key={i}
                    className="h-2 w-2 rounded-full bg-brand-300 animate-bounce"
                    style={{ animationDelay: `${i * 0.15}s` }}
                  />
                ))}
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Suggestions */}
      {messages.length === 1 && (
        <div className="px-4 py-2 border-t border-pawpal-border bg-pawpal-bg">
          <p className="mb-2 text-xs font-medium text-pawpal-muted">Try asking:</p>
          <div className="flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => useSuggestion(s)}
                className="rounded-full border border-pawpal-border bg-white px-3 py-1 text-xs text-pawpal-text hover:border-brand-300 hover:bg-brand-50 transition-colors"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        className="border-t border-pawpal-border bg-white px-4 py-3 flex gap-2"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about walks, feeding, grooming, medication..."
          className="flex-1 rounded-xl border border-pawpal-border px-4 py-2.5 text-sm text-pawpal-text placeholder:text-pawpal-muted focus:outline-none focus:ring-2 focus:ring-brand-300"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="rounded-xl bg-brand-500 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-brand-600 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Send
        </button>
      </form>
    </div>
  );
}
