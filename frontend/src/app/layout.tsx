import type { Metadata } from "next";
import "./globals.css";
import { Navigation } from "@/components/Navigation";

export const metadata: Metadata = {
  title: "Pre-Headline Intelligence | Story Formation & Narrative Provenance",
  description:
    "We don't just detect a story is emerging — we prove it, before it's obvious, in the language it's actually forming in.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#080C14] text-slate-100 flex flex-col antialiased">
        <Navigation />
        
        {/* Main Content Area */}
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>

        {/* Global Footer */}
        <footer className="w-full border-t border-slate-900 bg-[#06090F] py-6 mt-12 text-center text-xs text-slate-500 font-mono">
          <div className="max-w-7xl mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-3">
            <p>© 2026 Pre-Headline Intelligence — Story Formation & Narrative Provenance</p>
            <p className="text-slate-400 italic">
              "We didn't wait for the headline. We proved the story was forming."
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
