import React from "react";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import {
  FileCheck2,
  ChevronLeft,
  ShieldCheck,
  CheckCircle2,
  ExternalLink,
  BookOpen,
} from "lucide-react";

interface EvidencePageProps {
  params: {
    id: string;
  };
}

export default function EvidenceChainPage({ params }: EvidencePageProps) {
  const steps = [
    {
      step: 1,
      source: "Tamil Nadu Regional Daily (Dinamalar)",
      language: "Tamil (ta)",
      claim: "State environmental enforcement officers inspected manufacturing facility X on Tuesday morning.",
      supportingEvidence: "Direct quoting of field officer inspection log reference #TN-ENV-2026-88.",
      corroboration: "Primary on-the-ground regional reporting",
      confidence: 92,
    },
    {
      step: 2,
      source: "State Pollution Control Board Official Gazette",
      language: "English (en)",
      claim: "Notice of inquiry issued regarding emission compliance tolerances.",
      supportingEvidence: "Official regulatory public register document #PCB/ENF/441.",
      corroboration: "Primary government document confirming inspection premise",
      confidence: 98,
    },
    {
      step: 3,
      source: "Hindi Business Daily (Dainik Bhaskar)",
      language: "Hindi (hi)",
      claim: "Company X leadership summoned for formal compliance review.",
      supportingEvidence: "Corporate affairs ministry filing excerpt.",
      corroboration: "Independent multi-lingual cross-corroboration",
      confidence: 89,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Navigation breadcrumb */}
      <div>
        <Link href={`/stories/${params.id}`} className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors">
          <ChevronLeft className="w-3.5 h-3.5" /> Back to Story Detail
        </Link>
      </div>

      {/* Header section */}
      <div className="pb-6 border-b border-slate-800">
        <div className="flex flex-wrap items-center gap-2 mb-2">
          <Badge variant="primary" size="sm">PILLAR 2: MANDATORY EVIDENCE CHAIN</Badge>
          <Badge variant="success" size="sm">
            <CheckCircle2 className="w-3 h-3" /> Fully Corroborated
          </Badge>
        </div>
        <h1 className="text-2xl font-bold text-white">
          Provenance & Evidence Chain — Story {params.id}
        </h1>
        <p className="text-sm text-slate-400 mt-1 max-w-3xl">
          Structural verification chain required before any prediction or early intelligence alert is emitted.
          Flow: Source → Claim → Supporting Evidence → Corroboration → Confidence.
        </p>
      </div>

      {/* Chain Steps */}
      <div className="space-y-4">
        {steps.map((item) => (
          <Card key={item.step} variant="glass" className="p-6">
            <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
              <div className="flex items-start gap-4">
                <div className="w-8 h-8 rounded-full bg-blue-600/20 border border-blue-500/40 text-blue-400 flex items-center justify-center font-mono font-bold text-sm shrink-0">
                  {item.step}
                </div>
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-sm font-bold text-slate-100">{item.source}</h3>
                    <Badge variant="neutral" size="sm">{item.language}</Badge>
                  </div>
                  <div className="p-3 bg-surface-300 rounded-lg border border-slate-800 text-xs">
                    <span className="text-slate-400 font-mono block text-[10px] uppercase">EXTRACTED LOAD-BEARING CLAIM:</span>
                    <p className="text-slate-200 font-medium mt-0.5">"{item.claim}"</p>
                  </div>
                  <p className="text-xs text-slate-400">
                    <span className="font-semibold text-slate-300">Supporting Evidence:</span> {item.supportingEvidence}
                  </p>
                  <p className="text-xs text-slate-400">
                    <span className="font-semibold text-slate-300">Corroboration:</span> {item.corroboration}
                  </p>
                </div>
              </div>

              <div className="flex flex-col items-end justify-between shrink-0 font-mono text-xs">
                <span className="text-slate-500 text-[10px]">CONFIDENCE</span>
                <span className="text-emerald-400 font-bold text-base">{item.confidence}%</span>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
