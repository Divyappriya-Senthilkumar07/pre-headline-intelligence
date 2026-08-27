"use client";

import React, { useState, useRef } from "react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";

interface ExtractionItem {
  id: string;
  extraction_type: string;
  extracted_text?: string | null;
  confidence_score: number;
  metadata_json: Record<string, any>;
  created_at: string;
}

interface UploadedMedia {
  id: string;
  filename: string;
  media_type: string;
  mime_type: string;
  size: number;
  processing_status: string;
  created_at: string;
  extractions?: ExtractionItem[];
  processing_error?: string | null;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export function MediaUploader({ onUploadComplete }: { onUploadComplete?: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [notes, setNotes] = useState("");
  const [uploading, setUploading] = useState(false);
  const [statusPolling, setStatusPolling] = useState(false);
  const [currentMedia, setCurrentMedia] = useState<UploadedMedia | null>(null);
  const [activeExtraction, setActiveExtraction] = useState<ExtractionItem | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const getMediaType = (filename: string, mime: string) => {
    const ext = filename.split(".").pop()?.toLowerCase();
    if (["png", "jpg", "jpeg", "webp", "tiff"].includes(ext || "")) return "IMAGE";
    if (ext === "pdf" || mime.includes("pdf")) return "PDF";
    if (["txt", "md", "csv", "json"].includes(ext || "") || mime.startsWith("text/")) return "TEXT";
    if (["wav", "mp3", "m4a", "ogg", "flac"].includes(ext || "") || mime.startsWith("audio/")) return "AUDIO";
    if (["mp4", "mov", "avi", "webm"].includes(ext || "") || mime.startsWith("video/")) return "VIDEO";
    return "UNKNOWN";
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      setFile(selected);
      setErrorMsg(null);
      setCurrentMedia(null);
      setActiveExtraction(null);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      setErrorMsg(null);
      setCurrentMedia(null);
      setActiveExtraction(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setErrorMsg(null);

    const formData = new FormData();
    formData.append("file", file);
    if (notes.trim()) {
      formData.append("notes", notes.trim());
    }

    try {
      const res = await fetch(`${API_BASE}/media/upload`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Upload failed" }));
        throw new Error(err.detail || `Upload failed with status ${res.status}`);
      }

      const data: UploadedMedia = await res.json();
      setCurrentMedia(data);

      // Fetch full details with extractions
      await fetchMediaDetails(data.id);
      if (onUploadComplete) onUploadComplete();
    } catch (err: any) {
      setErrorMsg(err.message || "An unexpected error occurred during upload.");
    } finally {
      setUploading(false);
    }
  };

  const fetchMediaDetails = async (mediaId: string) => {
    try {
      const res = await fetch(`${API_BASE}/media/${mediaId}`);
      if (res.ok) {
        const fullData = await res.json();
        setCurrentMedia({
          id: fullData.id,
          filename: fullData.original_filename,
          media_type: fullData.media_type,
          mime_type: fullData.mime_type,
          size: fullData.file_size_bytes,
          processing_status: fullData.processing_status,
          created_at: fullData.upload_timestamp,
          extractions: fullData.extractions,
          processing_error: fullData.processing_error,
        });

        if (fullData.extractions && fullData.extractions.length > 0) {
          setActiveExtraction(fullData.extractions[0]);
        }
      }
    } catch (e) {
      console.error("Error fetching media details:", e);
    }
  };

  const handleRetry = async () => {
    if (!currentMedia) return;
    setStatusPolling(true);
    try {
      const res = await fetch(`${API_BASE}/media/${currentMedia.id}/retry`, {
        method: "POST",
      });
      if (res.ok) {
        await fetchMediaDetails(currentMedia.id);
      }
    } catch (e) {
      console.error("Error retrying media processing:", e);
    } finally {
      setStatusPolling(false);
    }
  };

  const handleDelete = async () => {
    if (!currentMedia) return;
    try {
      await fetch(`${API_BASE}/media/${currentMedia.id}`, {
        method: "DELETE",
      });
      setCurrentMedia(null);
      setActiveExtraction(null);
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      if (onUploadComplete) onUploadComplete();
    } catch (e) {
      console.error("Error deleting media:", e);
    }
  };

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-bold tracking-wide text-zinc-100 flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
            Analyst Media Ingestion
          </h2>
          <p className="text-xs text-zinc-400 mt-1">
            Accepts Images (OCR), PDFs, Plain Text, Audio, and Video files.
          </p>
        </div>
        <Badge variant="outline">Pipeline Ready</Badge>
      </div>

      {/* Drag & Drop Area */}
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
          file
            ? "border-emerald-500/60 bg-emerald-950/10"
            : "border-zinc-700/80 hover:border-zinc-500 bg-zinc-900/50 hover:bg-zinc-900/80"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          onChange={handleFileSelect}
          accept=".pdf,.png,.jpg,.jpeg,.txt,.md,.wav,.mp3,.mp4,.json,.csv"
        />

        {file ? (
          <div className="space-y-2">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-lg bg-emerald-500/20 text-emerald-400 font-mono text-xs font-bold uppercase">
              {getMediaType(file.name, file.type)}
            </div>
            <div className="text-sm font-medium text-zinc-200">{file.name}</div>
            <div className="text-xs text-zinc-400">
              {(file.size / 1024).toFixed(1)} KB • {file.type || "unknown mime"}
            </div>
            <p className="text-xs text-emerald-400/80 pt-1">Click or drag another file to replace</p>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-lg bg-zinc-800 text-zinc-400 text-xl font-bold">
              +
            </div>
            <div>
              <p className="text-sm text-zinc-300 font-medium">
                Click to browse or drag & drop analyst files
              </p>
              <p className="text-xs text-zinc-500 mt-1">
                Supported: PDF, PNG, JPG, TXT, MD, WAV, MP3, MP4 (Max 50MB)
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Analyst Notes Input */}
      {file && (
        <div className="mt-4">
          <label className="block text-xs font-medium text-zinc-400 mb-1">
            Analyst Context / Notes (Optional)
          </label>
          <input
            type="text"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="e.g. Received from regional enforcement leak, priority verify"
            className="w-full bg-zinc-900 border border-zinc-700/80 rounded-lg px-3 py-2 text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-zinc-500"
          />
        </div>
      )}

      {/* Upload Action Button */}
      {file && !currentMedia && (
        <div className="mt-4 flex justify-end">
          <Button
            variant="primary"
            onClick={handleUpload}
            disabled={uploading}
            className="w-full sm:w-auto"
          >
            {uploading ? (
              <span className="flex items-center gap-2">
                <LoadingSpinner size="sm" /> Uploading & Processing...
              </span>
            ) : (
              "Ingest & Extract Document"
            )}
          </Button>
        </div>
      )}

      {/* Error Message Display */}
      {errorMsg && (
        <div className="mt-4 p-3 rounded-lg bg-rose-950/40 border border-rose-800/60 text-xs text-rose-300 flex items-start gap-2">
          <span className="font-bold">Error:</span>
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Live Processing Status & Extraction Viewer */}
      {currentMedia && (
        <div className="mt-6 border-t border-zinc-800 pt-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-zinc-400">Media ID:</span>
              <span className="text-xs font-mono text-zinc-200">{currentMedia.id.slice(0, 12)}...</span>
            </div>
            <div className="flex items-center gap-2">
              <Badge
                variant={
                  currentMedia.processing_status === "COMPLETED"
                    ? "success"
                    : currentMedia.processing_status === "FAILED"
                    ? "danger"
                    : "warning"
                }
              >
                {currentMedia.processing_status}
              </Badge>
              {currentMedia.processing_status === "FAILED" && (
                <Button size="sm" variant="secondary" onClick={handleRetry} disabled={statusPolling}>
                  Retry
                </Button>
              )}
              <Button size="sm" variant="outline" onClick={handleDelete}>
                Delete
              </Button>
            </div>
          </div>

          {/* Diagnostic Error Details if Failed */}
          {currentMedia.processing_status === "FAILED" && currentMedia.processing_error && (
            <div className="p-3 rounded-lg bg-amber-950/30 border border-amber-800/40 text-xs text-amber-300">
              <div className="font-bold mb-1">Processing Diagnostic Notice:</div>
              <div>{currentMedia.processing_error}</div>
            </div>
          )}

          {/* Extracted Content Viewer */}
          {activeExtraction && (
            <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-4 space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-zinc-800 pb-2">
                <div className="flex items-center gap-2">
                  <Badge variant="default">{activeExtraction.extraction_type}</Badge>
                  {activeExtraction.metadata_json?.detected_language && (
                    <Badge variant="outline">
                      Lang: {activeExtraction.metadata_json.detected_language.toUpperCase()} (
                      {(activeExtraction.metadata_json.language_confidence * 100).toFixed(0)}%)
                    </Badge>
                  )}
                </div>
                <span className="text-[11px] font-mono text-zinc-400">
                  Confidence: {(activeExtraction.confidence_score * 100).toFixed(0)}%
                </span>
              </div>

              <div>
                <div className="text-xs font-medium text-zinc-400 mb-1">Extracted Normalized Text:</div>
                <div className="bg-zinc-900/80 rounded-lg p-3 text-xs text-zinc-200 font-mono whitespace-pre-wrap max-h-48 overflow-y-auto leading-relaxed border border-zinc-800">
                  {activeExtraction.extracted_text || (
                    <span className="text-zinc-500 italic">No direct textual content discovered.</span>
                  )}
                </div>
              </div>

              {activeExtraction.metadata_json && Object.keys(activeExtraction.metadata_json).length > 0 && (
                <div className="text-[11px] text-zinc-400 flex flex-wrap gap-3 pt-1 font-mono">
                  {Object.entries(activeExtraction.metadata_json).map(([k, v]) => {
                    if (typeof v === "object") return null;
                    return (
                      <span key={k} className="bg-zinc-900 px-2 py-0.5 rounded border border-zinc-800">
                        {k}: {String(v)}
                      </span>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </Card>
  );
}
