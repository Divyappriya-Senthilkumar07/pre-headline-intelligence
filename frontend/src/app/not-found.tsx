import React from "react";
import Link from "next/link";
import { FolderSearch, ChevronLeft } from "lucide-react";
import { Button } from "@/components/ui/Button";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] text-center p-8 space-y-4">
      <div className="p-4 rounded-full bg-slate-900 border border-slate-800 text-slate-400">
        <FolderSearch className="w-10 h-10 text-blue-400" />
      </div>
      <h2 className="text-xl font-bold text-slate-100">
        Intelligence Route Not Found
      </h2>
      <p className="text-sm text-slate-400 max-w-md">
        The requested story or evidence record does not exist in the active graph.
      </p>
      <Link href="/">
        <Button variant="primary">
          <ChevronLeft className="w-4 h-4 mr-1" /> Return to Feed
        </Button>
      </Link>
    </div>
  );
}
