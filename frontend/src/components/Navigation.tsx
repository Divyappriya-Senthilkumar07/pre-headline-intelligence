"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Radio,
  Layers,
  BookmarkCheck,
  BellRing,
  FileCheck2,
  PlayCircle,
  TrendingUp,
  Settings,
  Activity,
  Network,
  ShieldCheck,
} from "lucide-react";

export const Navigation: React.FC = () => {
  const pathname = usePathname();
  const [backendAlive, setBackendAlive] = useState<boolean | null>(null);

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const res = await fetch("http://localhost:8000/health");
        setBackendAlive(res.ok);
      } catch {
        setBackendAlive(false);
      }
    };
    checkBackend();
    const interval = setInterval(checkBackend, 30000);
    return () => clearInterval(interval);
  }, []);

  interface NavItem {
    label: string;
    href: string;
    icon: any;
    active: boolean;
    badge?: string;
  }

  const navItems: NavItem[] = [
    {
      label: "Intelligence Feed",
      href: "/",
      icon: Radio,
      active: pathname === "/",
    },
    {
      label: "Stories",
      href: "/stories",
      icon: Layers,
      active: pathname.startsWith("/stories"),
    },
    {
      label: "Watchlists",
      href: "/watchlists",
      icon: BookmarkCheck,
      active: pathname.startsWith("/watchlists"),
    },
    {
      label: "Alerts",
      href: "/alerts",
      icon: BellRing,
      active: pathname.startsWith("/alerts"),
    },
    {
      label: "Evidence",
      href: "/evidence",
      icon: FileCheck2,
      active: pathname.startsWith("/evidence"),
    },
    {
      label: "Historical Replay",
      href: "/replay",
      icon: PlayCircle,
      active: pathname.startsWith("/replay"),
    },
    {
      label: "Evaluation",
      href: "/evaluation",
      icon: TrendingUp,
      active: pathname.startsWith("/evaluation"),
    },
    {
      label: "Settings",
      href: "/settings",
      icon: Settings,
      active: pathname.startsWith("/settings"),
    },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-800 bg-[#080C14]/95 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo & Tagline */}
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-2.5 group">
              <div className="w-9 h-9 rounded-lg bg-cyan-600/20 border border-cyan-500/40 flex items-center justify-center text-cyan-400 shadow-glow group-hover:border-cyan-400 transition-colors">
                <Network className="w-5 h-5" />
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-bold tracking-wider text-slate-100 uppercase group-hover:text-cyan-400 transition-colors">
                  Pre-Headline Intel
                </span>
                <span className="text-[10px] text-slate-400 font-mono tracking-tight">
                  Story Formation Platform
                </span>
              </div>
            </Link>
          </div>

          {/* Navigation Links */}
          <nav className="hidden lg:flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    item.active
                      ? "bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 shadow-sm"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 border border-transparent"
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {item.label}
                  {item.badge && (
                    <span className="text-[9px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700 font-mono">
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>

          {/* Live System Pillar Status Pills (Analyst Observability) */}
          <div className="flex items-center gap-2.5">
            <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full bg-slate-900/80 border border-slate-800 text-[11px] font-mono text-slate-300">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span>Gate: ACTIVE</span>
            </div>

            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900/90 border border-slate-800 text-[11px] font-mono">
              <Activity className={`w-3.5 h-3.5 ${backendAlive ? "text-emerald-400" : "text-amber-400"}`} />
              <span className={backendAlive ? "text-emerald-400" : "text-amber-400"}>
                {backendAlive === null ? "Connecting..." : backendAlive ? "Backend OK" : "Offline"}
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
