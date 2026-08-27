"use client";

import React, { useState } from "react";
import { StickyNote, Plus, Trash2, CheckCircle, ShieldAlert, XCircle, Send, Check } from "lucide-react";

export interface StoryNoteItem {
  id: string;
  story_id: string;
  user_id: string;
  note: string;
  created_at: string;
}

interface AnalystNotesPanelProps {
  storyId: string;
  initialNotes: StoryNoteItem[];
  currentStatus: string;
  onStatusChange?: (newStatus: string) => void;
}

export const AnalystNotesPanel: React.FC<AnalystNotesPanelProps> = ({
  storyId,
  initialNotes,
  currentStatus,
  onStatusChange,
}) => {
  const [notes, setNotes] = useState<StoryNoteItem[]>(initialNotes);
  const [newNoteText, setNewNoteText] = useState("");
  const [statusVal, setStatusVal] = useState(currentStatus);
  const [submitting, setSubmitting] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNoteText.trim() || submitting) return;

    setSubmitting(true);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/stories/${storyId}/notes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ note: newNoteText }),
      });
      if (res.ok) {
        const added = await res.json();
        setNotes((prev) => [added, ...prev]);
        setNewNoteText("");
      }
    } catch (err) {
      console.error("Add note error:", err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteNote = async (noteId: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/stories/${storyId}/notes/${noteId}`, {
        method: "DELETE",
      });
      if (res.ok) {
        setNotes((prev) => prev.filter((n) => n.id !== noteId));
      }
    } catch (err) {
      console.error("Delete note error:", err);
    }
  };

  const handleUpdateStatus = async (targetStatus: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/stories/${storyId}/status`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: targetStatus }),
      });
      if (res.ok) {
        setStatusVal(targetStatus);
        onStatusChange?.(targetStatus);
        setStatusMsg(`Status updated to ${targetStatus}`);
        setTimeout(() => setStatusMsg(null), 3000);
      }
    } catch (err) {
      console.error("Status update error:", err);
    }
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-xl space-y-6">
      {/* Header & Status Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-lg bg-indigo-500/10 text-indigo-400">
            <StickyNote className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              Analyst Investigation & Notes
              <span className="text-xs px-2 py-0.5 rounded-full font-mono bg-slate-800 text-slate-400 border border-slate-700">
                PERSISTENT
              </span>
            </h3>
            <p className="text-xs text-slate-400">Human analyst verification notes and story disposition</p>
          </div>
        </div>

        {/* Status Actions */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-slate-400 font-medium">Disposition:</span>
          <button
            onClick={() => handleUpdateStatus("INVESTIGATING")}
            className={`px-3 py-1 rounded-lg text-xs font-semibold border transition-all ${
              statusVal === "INVESTIGATING"
                ? "bg-amber-500/20 text-amber-300 border-amber-500/50 ring-1 ring-amber-500/30"
                : "bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200"
            }`}
          >
            Investigate
          </button>
          <button
            onClick={() => handleUpdateStatus("ACKNOWLEDGED")}
            className={`px-3 py-1 rounded-lg text-xs font-semibold border transition-all ${
              statusVal === "ACKNOWLEDGED"
                ? "bg-cyan-500/20 text-cyan-300 border-cyan-500/50 ring-1 ring-cyan-500/30"
                : "bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200"
            }`}
          >
            Acknowledge
          </button>
          <button
            onClick={() => handleUpdateStatus("DISMISSED")}
            className={`px-3 py-1 rounded-lg text-xs font-semibold border transition-all ${
              statusVal === "DISMISSED"
                ? "bg-slate-700/60 text-slate-300 border-slate-600"
                : "bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200"
            }`}
          >
            Dismiss
          </button>
        </div>
      </div>

      {statusMsg && (
        <div className="p-2 rounded bg-emerald-950/30 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-1.5">
          <Check className="w-3.5 h-3.5" /> {statusMsg}
        </div>
      )}

      {/* Add Note Form */}
      <form onSubmit={handleAddNote} className="space-y-2">
        <textarea
          value={newNoteText}
          onChange={(e) => setNewNoteText(e.target.value)}
          placeholder="Add analyst observation, evidence verification link, or field notes..."
          rows={2}
          className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
        />
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={submitting || !newNoteText.trim()}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold disabled:opacity-50 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" /> Add Note
          </button>
        </div>
      </form>

      {/* Notes List */}
      <div className="space-y-3">
        {notes.length === 0 ? (
          <p className="text-xs text-slate-500 italic">No notes added by analysts yet.</p>
        ) : (
          notes.map((n) => (
            <div
              key={n.id}
              className="p-3.5 rounded-xl bg-slate-800/40 border border-slate-800 flex items-start justify-between gap-4"
            >
              <div className="space-y-1">
                <p className="text-xs text-slate-200 leading-relaxed">{n.note}</p>
                <span className="text-[10px] text-slate-500 font-mono block">
                  {n.user_id} • {new Date(n.created_at).toLocaleString()}
                </span>
              </div>
              <button
                onClick={() => handleDeleteNote(n.id)}
                className="p-1 text-slate-500 hover:text-rose-400 transition-colors shrink-0"
                title="Delete note"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
