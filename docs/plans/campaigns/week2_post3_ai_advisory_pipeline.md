# FolioGuard — LinkedIn Campaign: Week 2, Post 3 (3-Stage AI Advisory Pipeline)

> **Campaign Phase:** Week 2 — AI Engineering & Frontend UX  
> **Post Number:** 3 of 10  
> **Target Day:** Tuesday  
> **Ideal Posting Window:** 08:30 AM – 09:30 AM IST (or 06:30 PM – 07:30 PM IST)  
> **Author:** Benoi Rajan  
> **Core Objective:** Demonstrate production-grade AI engineering (multi-pass reasoning, strict Pydantic guardrails, deterministic pre-flight rules, and real-time SSE streaming) to attract AI/ML engineers, full-stack leads, and fintech builders.  
> **Key Visual Assets:**  
> 1. [06_advisory_tab.png](file:///home/benoi/Projects/Folio_guard/.reports/e2e_screenshots/06_advisory_tab.png) — Live UI screenshot of the 3-Stage AI Advisory Wizard.  
> 2. Mermaid Pipeline Diagram & AI Image Generation Prompts ([Visual Assets Below](#-visual-assets--image-generation-prompts)).

---

## 📱 Final LinkedIn Post Copy (Ready to Publish)

*(Copy and paste the exact text below into LinkedIn)*

```text
Prompting an LLM to "analyze my stock portfolio and tell me what to buy" is a recipe for hallucinations and financial disaster.

In a single-pass prompt, LLMs routinely:
• Invent non-existent NSE ticker symbols
• Ignore hard concentration limits (e.g., 30% in one stock)
• Suggest fractional shares or blow past your available cash budget
• Mix macro diagnosis with impulsive trade execution

When building FolioGuard's AI Advisory Engine, I replaced single-shot prompting with a deterministic-first, 3-stage Google Gemini pipeline enforced by strict Pydantic schemas.

Here is how the pipeline works under the hood:

0. 🛡️ Pre-Flight Deterministic Rule Engine
Before an LLM ever sees the portfolio, Python evaluates hard risk boundaries (single-stock caps, sector concentration limits, and technical guardrails) so math and risk thresholds are never hallucinated.

1. 🔍 Stage 1 — Portfolio Diagnosis (No Trade Decisions)
Gemini audits overall portfolio quality, sector health, individual stock fundamentals, and live news context — outputting a structured `Stage1Diagnosis` schema. Its only job is objective diagnosis.

2. 🔎 Stage 2 — Opportunity Screening & NSE Validation
Using Stage 1's findings, the model screens existing holdings and new candidates, classifying each into strict conviction tiers (`HIGH_CONVICTION`, `GOOD_OPPORTUNITY`, `WATCHLIST`, `AVOID_FOR_NOW`) while validating ticker symbols against live NSE market data.

3. 🧮 Stage 3 — Budget-Capped Execution (`Stage3Execution`)
The final pass translates ranked opportunities into whole-share allocations (`BUY`, `PARTIALLY_INVEST`, or `WAIT`), enforcing exact budget limits, cash buffers, and deterministic sanity checks.

4. ⚡ Real-Time SSE Streaming (`/api/v1/advisory/stream`)
Running 3 sequential LLM passes takes time. Instead of a spinning loader that times out, FastAPI streams live stage-by-stage progress to the Next.js 14 UI via Server-Sent Events (SSE), updating each wizard step the moment it completes.

Good AI engineering isn't about writing a cleverer prompt — it's about constraining the model with deterministic guardrails, typed contracts, and graceful fallbacks.

How are you preventing LLM hallucinations in production workflows? Structured outputs, multi-pass chains, or deterministic pre-filters?

Let's discuss below! 👇

#ai #generativeai #gemini #pydantic #python #fastapi #fintech #promptengineering #softwareengineering #buildinpublic
```

---

## 💬 First Comment Templates (Choose One)

> [!TIP]
> **Why post links in the first comment?**  
> LinkedIn’s feed algorithm deprioritizes posts with external outbound links in the caption. Posting the live app and repo in the first comment ensures maximum reach.

### Option 1: Technical Deep-Dive & Live Demo (Recommended)
```text
Want to see the 3-stage SSE streaming wizard in action?

🌐 Live App Demo: https://portfolio-assistant-rouge.vercel.app
💻 GitHub Repository: https://github.com/benoirajan/portfolio-assistant

Key Files to Inspect in the Repo:
• Pipeline & Pydantic Schemas: `backend/src/services/llm_advisor.py`
• SSE Streaming Endpoint: `backend/src/api/advisory.py` (`/api/v1/advisory/stream`)

If you'd like a breakdown of how we handle Upstash Redis rate-limiting (10 req/min) and deterministic fallbacks when LLM quotas are hit, drop a comment!
```

### Option 2: Engagement & Schema Handout
```text
🌐 Try the live 3-Stage AI Advisor here: https://portfolio-assistant-rouge.vercel.app

I structured the entire 3-stage pipeline with strict Pydantic v2 models (`Stage1Diagnosis`, `Stage2Ranking`, `Stage3Execution`) and SSE streaming in FastAPI.

Comment "PIPELINE" below if you want the direct link to the Pydantic schemas and prompt architecture!
```

---

## 🎨 Visual Assets & Image Generation Prompts

You can attach the live UI screenshot ([06_advisory_tab.png](file:///home/benoi/Projects/Folio_guard/.reports/e2e_screenshots/06_advisory_tab.png)), a crisp Mermaid pipeline export, or a custom AI-generated graphic using the prompts below.

### Option A: Live Product Screenshot (Ready to Upload)
* **File Path:** [`06_advisory_tab.png`](file:///home/benoi/Projects/Folio_guard/.reports/e2e_screenshots/06_advisory_tab.png)
* **LinkedIn Image Alt Text:** `FolioGuard 3-Stage AI Advisory dashboard showing real-time portfolio diagnosis, opportunity screening, and budget-capped execution steps`

---

### Option B: Clean Mermaid Pipeline Diagram (Native & Crisp)
*Render this in [mermaid.live](https://mermaid.live) and export as a high-res PNG/SVG:*

```mermaid
flowchart LR
    Input(["User Portfolio + Goal\n+ Budget Cap"]) --> Rules["0. Deterministic Rule Engine\n(Stock/Sector Caps)"]
    Rules --> S1["Stage 1: Diagnosis\n(Stage1Diagnosis)\nMacro & Risk Audit"]
    S1 -->|"SSE Event 1"| S2["Stage 2: Screening\n(Stage2Ranking)\nNSE Symbol Validation"]
    S2 -->|"SSE Event 2"| S3["Stage 3: Execution\n(Stage3Execution)\nWhole-Share Allocation"]
    S3 -->|"SSE Event 3"| UI["Next.js 14 Advisory Wizard\n(Real-Time Stream)"]

    classDef stage fill:#1e293b,stroke:#3b82f6,stroke-width:2px,color:#f8fafc;
    classDef guard fill:#0f172a,stroke:#10b981,stroke-width:2px,color:#f8fafc;
    classDef io fill:#020617,stroke:#8b5cf6,stroke-width:2px,color:#f8fafc;
    class S1,S2,S3 stage;
    class Rules guard;
    class Input,UI io;
```

---

### Option C: AI Image Generation Prompts (Midjourney / DALL-E 3 / Imagen 3)

#### Prompt 1: Isometric 3-Stage AI Pipeline Architecture (Recommended)
```text
An isometric 3D dark-mode technical illustration of a 3-stage AI advisory pipeline for a modern fintech application. Sleek obsidian slate background (#0B1120). Three glowing glassmorphic stages connected by luminous cyan and emerald fiber-optic data streams: Stage 1 (a magnifying glass over a portfolio shield labeled "DIAGNOSIS"), Stage 2 (a precision filter funnel sorting glowing stock ticker nodes labeled "SCREENING"), and Stage 3 (a deterministic calculator and execution ledger labeled "EXECUTION"). Protecting the entrance is a glowing emerald hexagonal firewall representing "Pydantic Guardrails". Ultra-crisp enterprise SaaS aesthetic, subtle depth of field, volumetric lighting, octane render, 8k --ar 16:9
```

#### Prompt 2: Minimalist Fintech Infographic — "Single Prompt vs. 3-Stage Pipeline"
```text
A clean, modern minimalist tech infographic on a deep charcoal background comparing two AI architectures side by side. Left side (muted red/amber): a chaotic tangled knot of glowing lines labeled "Single-Pass Prompt" with warning icons. Right side (crisp electric blue and emerald green): a structured, three-step modular pipeline with clean glassmorphic cards connected by straight glowing arrows, representing Deterministic Rules -> Diagnosis -> Screening -> Execution. Professional developer LinkedIn graphic, flat 3D vector aesthetic, high contrast, crisp layout, 8k --ar 1200:627
```

#### Prompt 3: Real-Time SSE Streaming & Neural Guardrail Concept
```text
A futuristic conceptual 3D render of a glowing neural AI core (purple and blue Gemini-inspired aura) encased inside a precise geometric titanium and emerald-green lattice cage, representing strict Pydantic type guardrails constraining an LLM. From the core, three distinct streams of structured golden and cyan data packets flow sequentially into a sleek dark-mode financial dashboard interface. Dark studio background, cinematic rim lighting, ultra-sharp glass and metal textures, 8k --ar 16:9
```

---

## 🔄 Alternative Hooks (For Reference / Future Iteration)

### Option B — The "Pydantic Guardrails" Hook
> *"Most AI demos break the moment you put them in front of real financial data. Here is how we used Pydantic v2 schemas and a 3-pass Google Gemini pipeline to turn unstructured LLM reasoning into deterministic, whole-share portfolio actions."*

### Option C — The "UX of Slow AI" (SSE Streaming) Hook
> *"What do you do when your AI pipeline takes 15 seconds across 3 reasoning passes? You don't show a spinner and pray it doesn't time out. You stream every stage live with FastAPI Server-Sent Events (SSE)."*

---

## ⏱️ Pre-Publishing & Post-Publishing Protocol

### 15 Minutes Before Publishing
1. [ ] Verify [`https://portfolio-assistant-rouge.vercel.app`](https://portfolio-assistant-rouge.vercel.app) is warm and the Advisory tab streams cleanly.
2. [ ] Have your chosen First Comment copied to your clipboard.

### Moment of Publishing
1. [ ] Paste the post copy and verify line breaks on LinkedIn desktop preview.
2. [ ] Attach [06_advisory_tab.png](file:///home/benoi/Projects/Folio_guard/.reports/e2e_screenshots/06_advisory_tab.png) (or your generated pipeline graphic) and add Alt Text.
3. [ ] Click **Post** and immediately drop the **First Comment** within 30 seconds.

### First 60 Minutes (Critical Algorithm Window)
1. [ ] Reply promptly to questions about Pydantic validation, NSE symbol grounding, or SSE streaming in FastAPI.
