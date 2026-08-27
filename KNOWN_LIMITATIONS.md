# Pre-Headline Intelligence — Known Limitations & Operational Boundaries

In accordance with product principles, this document transparently enumerates the technical and operational boundaries of the Pre-Headline Intelligence platform.

---

## 1. Labeled Evaluation Dataset Sample Size
- **Current State**: The current benchmark suite operates on 6 structured, deterministic seed evaluation scenarios (comprising multi-source Indic and English events).
- **Limitation**: While all 6 scenarios rigorously test specific mechanics (lead time, syndication traps, contradiction blocking, multilingual convergence, false signals, missed stories), sample sizes for calibration probability bins are small ($n < 20$).
- **Safeguard**: The Evaluation Dashboard explicitly displays a *"Limited evaluation sample ($n < 20$)"* notice. The system refuses to display fake statistical precision when data is limited.

## 2. Indic Vernacular OCR & Audio Transcription Fidelity
- **Current State**: The media pipeline includes extractors for Images (Tesseract OCR), PDFs (pypdf/pdfminer), and Audio/Video (Whisper / Speech recognition wrappers).
- **Limitation**: Low-resolution scanned regional newspapers (e.g. micro-print Tamil or Hindi dailies) or low-bitrate audio recordings from community radios may suffer degraded character error rates (CER).
- **Safeguard**: When extraction confidence falls below threshold, the media processing status explicitly marks `FAILED` or `PARTIAL_EXTRACTION` with full error provenance — the system **never fabricates or hallucinates text**.

## 3. Flash Breaking Events Without Prior Precursors (Black Swan Detection)
- **Current State**: The platform's core capability is detecting story formation across weak precursor signals (local reports, regulatory filings, vernacular discussions).
- **Limitation**: Sudden, instantaneous breaking events (e.g. natural disasters, unexpected flash corporate resignations) that break directly onto national wires without prior local discussion cannot be detected with positive lead time.
- **Safeguard**: As demonstrated in Scenario 6, the system honestly classifies such events as `MISSED_STORY` with root cause `SUDDEN_FLASH_NO_PRIOR_SIGNAL`, rather than pretending to predict the un-predictable.

## 4. Source Independence Ownership Tree Coverage
- **Current State**: Agent 5 resolves parent conglomerate ownership across major wire services, regional media networks, and syndicated aggregators.
- **Limitation**: Unregistered shell publishers, undisclosed private equity holding companies, or coordinated sockpuppet networks that do not share public domain ownership metadata may initially register as distinct desks until content hash similarity triggers deduplication.
- **Safeguard**: Content hash fingerprinting and near-duplicate text similarity run alongside publisher metadata to catch syndicated copies even when domain ownership is obscured.

## 5. LLM Reasoning Latency & Rate Limits
- **Current State**: The Grounded Copilot (Agent 8) and Narrative Formation (Agent 6) utilize LLM reasoning.
- **Limitation**: Under high concurrent load, external provider API rate limits or latency spikes ($> 2\text{ seconds}$) may occur.
- **Safeguard**: All LLM queries use deterministic caching based on `story_id` + `evidence_hash` + normalized query. Repeated queries return sub-millisecond cached responses with zero token expenditure.
