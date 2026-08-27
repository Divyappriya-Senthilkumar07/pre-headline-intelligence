import React from "react";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import {
  ShieldAlert,
  AlertTriangle,
  ChevronLeft,
  Scale,
  XCircle,
  FileWarning,
} from "lucide-react";

interface ContradictionPageProps {
  params: {
    id: string;
  };
}

export default function ContradictionMonitorPage({ params }: ContradictionPageProps) {
  return (
    <div className="space-y-6">
      {/* Navigation breadcrumb */}
      <div>
        <Link href="/" className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors">
          <ChevronLeft className="w-3.5 h-3.5" /> Back to Intelligence Feed
        </Link>
      </div>

      {/* Header section */}
      <div className="pb-6 border-b border-slate-800">
        <div className="flex flex-wrap items-center gap-2 mb-2">
          <Badge variant="danger" size="sm">PILLAR 3: CONTRADICTION GATE</Badge>
          <Badge variant="danger" size="sm">
            <AlertTriangle className="w-3 h-3" /> HARD STOP TRIGGERED
          </Badge>
        </div>
        <h1 className="text-2xl font-bold text-white">
          Contradiction Gate Monitor — Story {params.id}
        </h1>
        <p className="text-sm text-slate-400 mt-1 max-w-3xl">
          When credible sources directly conflict on a load-bearing claim, the system halts prediction and surfaces the conflict instead of averaging it away.
        </p>
      </div>

      {/* Warning Banner */}
      <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
        <div className="text-xs space-y-1">
          <p className="font-bold text-rose-200 uppercase tracking-wide">
            Automated Prediction Halted (Code Guard Clause Active)
          </p>
          <p className="text-rose-300">
            A direct factual conflict exists between Source A and Official Gazette Source B on a load-bearing permit renewal claim. Predictions are blocked from emission until analyst resolution.
          </p>
        </div>
      </div>

      {/* Side-by-Side Conflicting Claims */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
        {/* Source A */}
        <Card variant="default" className="p-6 space-y-3 border-slate-700">
          <div className="flex items-center justify-between">
            <Badge variant="neutral" size="sm">SOURCE A (REGIONAL NEWS)</Badge>
            <span className="text-xs text-slate-400 font-mono">08:00 AM</span>
          </div>
          <h3 className="text-sm font-bold text-slate-100">Local District Daily Report</h3>
          <div className="p-3 bg-surface-300 rounded-lg border border-slate-800 text-xs">
            <p className="text-slate-200">
              "Company X facility operations cleared following routine annual environmental license renewal."
            </p>
          </div>
          <p className="text-xs text-slate-400">
            <span className="font-semibold text-slate-300">Claim Type:</span> Corporate Statement Excerpt
          </p>
        </Card>

        {/* Source B (Conflicting) */}
        <Card variant="danger" className="p-6 space-y-3">
          <div className="flex items-center justify-between">
            <Badge variant="danger" size="sm">SOURCE B (OFFICIAL GAZETTE)</Badge>
            <span className="text-xs text-rose-400 font-mono">08:30 AM</span>
          </div>
          <h3 className="text-sm font-bold text-rose-100">State Pollution Control Board Gazette</h3>
          <div className="p-3 bg-surface-300 rounded-lg border border-rose-500/30 text-xs">
            <p className="text-rose-200 font-semibold">
              "Operational permit for facility X suspended pending compliance inquiry #PCB/ENF/441."
            </p>
          </div>
          <p className="text-xs text-slate-400">
            <span className="font-semibold text-slate-300">Claim Type:</span> Regulatory Legal Notice (Load-Bearing)
          </p>
        </Card>
      </div>
    </div>
  );
}
