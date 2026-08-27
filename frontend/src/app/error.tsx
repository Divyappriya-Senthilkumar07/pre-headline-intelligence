"use client";

import React, { useEffect } from "react";
import { AlertCircle, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/Button";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Platform application error:", error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] text-center p-8 space-y-4">
      <div className="p-4 rounded-full bg-rose-500/10 border border-rose-500/30 text-rose-400">
        <AlertCircle className="w-10 h-10" />
      </div>
      <h2 className="text-xl font-bold text-slate-100">
        Intelligence Signal Error
      </h2>
      <p className="text-sm text-slate-400 max-w-md">
        An unexpected error occurred while loading this view. The pipeline remains guarded.
      </p>
      <Button variant="secondary" onClick={() => reset()}>
        <RotateCcw className="w-4 h-4 mr-2" /> Retry Connection
      </Button>
    </div>
  );
}
