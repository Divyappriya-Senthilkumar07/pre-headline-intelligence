"use client";

import React, { useState } from "react";
import { Bot, Send, Sparkles, AlertCircle, Bookmark, CheckCircle2, RefreshCw } from "lucide-react";

export interface CitationItem {
  source_name: string;
  evidence_type: string;
  reference_id: string;
  excerpt: string;
}

export interface CopilotMessage {
  id: string;
  sender: "user" | "copilot";
  text: string;
  is_refusal?: boolean;
  refusal_reason?: string | null;
  citations?: CitationItem[];
  cached?: boolean;
  timestamp: Date;
}

interface CopilotPanelProps {
  storyId: string;
  storyTitle: string;
}

const PRESET_QUERIES = [
  "Why did this story receive a high formation score?",
  "How many independent sources support this?",
  "What evidence supports the main claim?",
  "Why is the prediction blocked or what contradiction exists?",
  "What is Company X's stock price today?", // tests ungrounded refusal rule
];

export const CopilotPanel: React.FC<CopilotPanelProps> = ({ storyId, storyTitle }) => {
  const [messages, setMessages] = useState<CopilotMessage[]>([
    {
      id: "initial-msg",
      sender: "copilot",
      text: `Hello Analyst. I am the Grounded Story Copilot for '${storyTitle}'. My answers are strictly constrained to the verified evidence in this story cluster. I will refuse to speculate or answer questions outside the verified evidence.`,
      timestamp: new Date(),
    },
  ]);
  const [inputQuery, setInputQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async (queryText?: string) => {
    const q = (queryText || inputQuery).trim();
    if (!q || isLoading) return;

    const userMsg: CopilotMessage = {
      id: `user-${Date.now()}`,
      sender: "user",
      text: q,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery("");
    setIsLoading(true);

    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/copilot/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          story_id: storyId,
          question: q,
        }),
      });

      if (!res.ok) {
        throw new Error(`Copilot query error: ${res.statusText}`);
      }

      const data = await res.json();
      const copilotMsg: CopilotMessage = {
        id: `copilot-${Date.now()}`,
        sender: "copilot",
        text: data.answer,
        is_refusal: data.is_refusal,
        refusal_reason: data.refusal_reason,
        citations: data.citations || [],
        cached: data.cached,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, copilotMsg]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: "copilot",
          text: `Error contacting Copilot service: ${err.message}`,
          is_refusal: true,
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-xl flex flex-col h-[520px]">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-3 shrink-0">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-teal-500/10 text-teal-400">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              Agent 8: Grounded Analyst Copilot
              <span className="text-[10px] px-2 py-0.5 rounded-full font-mono bg-teal-500/20 text-teal-300 border border-teal-500/40">
                ZERO-HALLUCINATION
              </span>
            </h3>
            <p className="text-xs text-slate-400">Scoped exclusively to this story cluster's verified evidence graph</p>
          </div>
        </div>
      </div>

      {/* Suggested Query Pills */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-2 mb-2 shrink-0 no-scrollbar">
        <span className="text-[10px] text-slate-500 font-mono uppercase flex items-center gap-1 shrink-0">
          <Sparkles className="w-3 h-3 text-amber-400" /> Presets:
        </span>
        {PRESET_QUERIES.map((preset, i) => (
          <button
            key={i}
            onClick={() => handleSend(preset)}
            disabled={isLoading}
            className="text-[11px] px-2.5 py-1 rounded-full bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700/60 whitespace-nowrap transition-colors shrink-0 disabled:opacity-50"
          >
            {preset}
          </button>
        ))}
      </div>

      {/* Chat Messages Log */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-1">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${msg.sender === "user" ? "items-end" : "items-start"}`}
          >
            <div
              className={`max-w-[88%] p-3.5 rounded-xl text-xs leading-relaxed ${
                msg.sender === "user"
                  ? "bg-teal-600/90 text-white rounded-br-none shadow"
                  : msg.is_refusal
                  ? "bg-rose-950/30 border border-rose-500/40 text-rose-200 rounded-bl-none"
                  : "bg-slate-800/70 border border-slate-700/60 text-slate-200 rounded-bl-none"
              }`}
            >
              {msg.is_refusal && (
                <div className="flex items-center gap-1.5 font-semibold text-rose-300 mb-1">
                  <AlertCircle className="w-3.5 h-3.5" />
                  Negative Refusal Triggered (Out of Grounded Scope)
                </div>
              )}

              <p>{msg.text}</p>

              {/* Citations Footer if present */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-2.5 pt-2 border-t border-slate-700/60 space-y-1">
                  <span className="text-[10px] font-mono uppercase text-teal-400 flex items-center gap-1">
                    <Bookmark className="w-2.5 h-2.5" /> Grounded Citations ({msg.citations.length}):
                  </span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {msg.citations.map((c, idx) => (
                      <span
                        key={idx}
                        className="text-[10px] px-1.5 py-0.5 rounded bg-slate-900/80 text-slate-300 border border-slate-700 font-mono"
                        title={c.excerpt}
                      >
                        [{c.source_name}]
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {msg.cached && (
                <div className="mt-1 text-[9px] font-mono text-slate-500 flex items-center gap-1">
                  <RefreshCw className="w-2.5 h-2.5" /> Served from deterministic evidence cache
                </div>
              )}
            </div>
            <span className="text-[9px] text-slate-500 mt-1 px-1 font-mono">
              {msg.sender === "user" ? "Analyst" : "Copilot"} • {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
        ))}

        {isLoading && (
          <div className="flex items-center space-x-2 text-xs text-teal-400 font-mono p-2">
            <div className="w-2 h-2 rounded-full bg-teal-400 animate-bounce" />
            <div className="w-2 h-2 rounded-full bg-teal-400 animate-bounce [animation-delay:0.2s]" />
            <div className="w-2 h-2 rounded-full bg-teal-400 animate-bounce [animation-delay:0.4s]" />
            <span className="ml-2">Grounding response against story evidence graph...</span>
          </div>
        )}
      </div>

      {/* Input Box */}
      <div className="pt-3 border-t border-slate-800 shrink-0">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            placeholder="Ask anything about this story's sources, claims, contradictions, or scores..."
            disabled={isLoading}
            className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-teal-500 transition-colors disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isLoading || !inputQuery.trim()}
            className="p-2 rounded-lg bg-teal-600 hover:bg-teal-500 text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
