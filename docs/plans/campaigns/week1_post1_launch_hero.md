# FolioGuard — LinkedIn Campaign: Week 1, Post 1 (Launch & Hero)

> **Campaign Phase:** Week 1 — System Introduction & Architecture  
> **Post Number:** 1 of 10  
> **Target Day:** Tuesday  
> **Ideal Posting Window:** 08:30 AM – 09:30 AM IST (or 06:30 PM – 07:30 PM IST)  
> **Author:** Benoi Rajan  
> **Core Objective:** Launch hero announcement, drive live app trials, and establish technical authority as a full-stack fintech engineer.  
> **Key Visual Assets:**
> 1. [folioguard_launch_infographic.png](file:///home/benoi/Projects/Folio_guard/docs/plans/campaigns/assets/folioguard_launch_infographic.png) — High-res 1200x675 Launch Infographic (contains feature pills, tech stack, and framed UI preview).
> 2. [folioguard_3d_hero_graphic.jpg](file:///home/benoi/Projects/Folio_guard/docs/plans/campaigns/assets/folioguard_3d_hero_graphic.jpg) — 3D Glassmorphic Concept Graphic (cybernetic financial nodes, candlestick trends, metrics).
> 3. [01_landing_page.png](file:///home/benoi/Projects/Folio_guard/.reports/e2e_screenshots/01_landing_page.png) — Clean 1440x950 raw desktop UI render.

---

## 📱 Final LinkedIn Post Copy (Ready to Publish)

*(Copy and paste the exact text below into LinkedIn)*

```text
Most retail equity investors in India open their Zerodha Demat, see a green daily P&L, and assume their portfolio is in great shape.

They don't realize:
• Their portfolio Beta is 1.6 (amplifying market dips by 60%)
• 45% of their net worth is concentrated in a single sector
• Their actual annualized return (XIRR) trails a plain NIFTY index fund
• They are sitting on harvestable tax losses before March 31st

I decided to fix that.

Over the past few weeks, I built and deployed FolioGuard — a production-ready, AI-powered portfolio assistant engineered specifically for Indian equity investors.

Here is what it does under the hood:

1. ⚡ Instant Demat Sync & Ingestion
Seamlessly imports Zerodha Kite portfolios with zero credential retention and Fernet AES-256 encryption at rest.

2. 📊 Deterministic Quantitative Risk Engine
Calculates true XIRR via Newton-Raphson approximation, portfolio Beta against the NIFTY 50, and Sharpe & Sortino ratios against 10Y Indian G-Sec yields. No hallucinations, pure financial math.

3. 🤖 3-Stage Google Gemini Advisory Pipeline
A multi-pass reasoning engine with strict Pydantic schemas:
• Stage 1: Macro & concentration risk diagnosis
• Stage 2: Symbol screening against live NSE market data
• Stage 3: Budget-capped whole-share trade generation

4. 📉 Automated Tax-Loss Harvesting (Union Budget 2024 Rules)
Classifies holdings into STCG (20%) and LTCG (12.5%), tracking gains against the ₹1.25L exemption ceiling and suggesting harvestable loss candidates.

5. ☁️ Zero-Maintenance Serverless Cloud Architecture
• Frontend: Next.js 14 App Router on Vercel Edge
• Backend: Dockerized FastAPI on Google Cloud Run (asia-south1)
• Persistence: Supabase PostgreSQL (transaction pooled) + Upstash Redis (rate limiting & caching)
• Reliability: 49 automated unit tests and GitHub Actions CI/CD with health check gates.

FolioGuard was built solo from 0 to production to bridge the gap between retail investing and institutional-grade analytics.

The live app is free to explore — check the first comment below for the demo link!

What is the biggest blind spot you’ve encountered in your personal portfolio tracking? Let me know in the comments. 👇

#buildinpublic #fintech #fullstack #nextjs #fastapi #python #ai #softwareengineering #wealthtech #investing
```

---

## 💬 First Comment Templates (Choose One)

> [!TIP]
> **Why post links in the first comment?**  
> LinkedIn’s feed algorithm deprioritizes posts with external outbound links in the caption. Posting the live app and repo in the first comment ensures maximum algorithmic distribution while keeping links easily accessible.

### Option 1: Full Transparency (Recommended for Technical Credibility)
```text
Explore the live app and inspect the project here:

🌐 Live App Demo: https://portfolio-assistant-rouge.vercel.app
💻 GitHub Repository: https://github.com/benoirajan/portfolio-assistant

Tech Stack at a glance:
• Frontend: Next.js 14, Tailwind CSS, Recharts
• Backend: Python, FastAPI, SQLAlchemy 2.0, Alembic
• AI Engine: Google Gemini API (google-genai)
• DB & Cache: Supabase PostgreSQL 16, Upstash Redis
• Broker API: Zerodha Kite Connect SDK

Feedback, thoughts, and PRs are always welcome!
```

### Option 2: Engagement-Booster (Drives Comment Volume)
```text
🌐 Try the live demo directly here: https://portfolio-assistant-rouge.vercel.app

Interested in the source code, system architecture diagrams, or the 3-stage Gemini prompt schemas?

Drop a comment with "REPO" below and I’ll send you the direct GitHub link and technical breakdown!
```

---

## 🎨 Media Assets & Upload Options

You have two tailored visual options generated for this post, depending on your preferred posting style:

### Option 1 (Recommended): Launch Infographic with UI Mockup & Features
* **File Path:** [`docs/plans/campaigns/assets/folioguard_launch_infographic.png`](file:///home/benoi/Projects/Folio_guard/docs/plans/campaigns/assets/folioguard_launch_infographic.png)
* **Format & Dimensions:** 1200 × 675 px (16:9 LinkedIn standard banner)
* **Contents & Graphics:**
  - Header: `FolioGuard` title with `PRODUCTION LAUNCH` live pill.
  - 4 Key Feature Cards with color-coded accent indicators:
    - 🤖 *3-Stage Gemini Advisory* (Pre-flight guards → NSE screening → Budget-capped orders)
    - 📊 *Deterministic Math Engine* (Newton-Raphson XIRR, Beta vs NIFTY 50, Sharpe & Sortino)
    - 📉 *Tax-Loss Harvesting* (Budget 2024 rules: STCG 20%, LTCG 12.5%, ₹1.25L exemption)
    - ⚡ *Zerodha Kite Ingestion* (Zero credential retention + Fernet AES-256 encryption)
  - Framed Browser Mockup showcasing the actual live landing page ([`01_landing_page.png`](file:///home/benoi/Projects/Folio_guard/.reports/e2e_screenshots/01_landing_page.png))
  - Bottom Technology Stack Badges: `Next.js 14`, `FastAPI`, `Cloud Run`, `Supabase`, `Upstash`, `Gemini`
  - Footer attribution: *Crafted by Benoi Rajan · Full-Stack & AI Systems* + Live Demo link
* **LinkedIn Image Alt Text:** `FolioGuard launch infographic featuring platform overview, architecture badges, and dashboard preview for Indian equity investors`

### Option 2: 3D Conceptual Glassmorphic Hero
* **File Path:** [`docs/plans/campaigns/assets/folioguard_3d_hero_graphic.jpg`](file:///home/benoi/Projects/Folio_guard/docs/plans/campaigns/assets/folioguard_3d_hero_graphic.jpg)
* **Format:** High-resolution 3D glassmorphic dark-mode illustration with floating metric cards (XIRR +24.8%, Beta 1.02, Rupee indicators, and glowing emerald/cyan data streams).
* **LinkedIn Image Alt Text:** `Futuristic 3D financial analytics dashboard with glowing metrics and candlestick charts representing FolioGuard`

*(Tip: You can also attach both images as a multi-image post or upload them as a 2-slide PDF carousel document for enhanced engagement).*

---

## 🔄 Alternative Hooks (For Reference / Future Iteration)

### Option B — The Solo Builder & Velocity Hook
> *"Can one engineer build, test, and deploy a 10-microservice fintech platform from scratch in a few weeks? Here’s why I built FolioGuard — an institutional-grade portfolio intelligence assistant with Next.js 14, FastAPI, and Google Gemini."*

### Option C — The "AI Toy vs Production Guardrail" Hook
> *"Most 'AI finance' apps are shallow ChatGPT wrappers that hallucinate stock prices and give risky advice. When building FolioGuard, I enforced a strict rule: deterministic financial math handles the numbers, while a 3-stage Pydantic-guarded Gemini pipeline handles the advisory."*

---

## ⏱️ Pre-Publishing & Post-Publishing Protocol

### 15 Minutes Before Publishing
1. [ ] Test the live demo URL: [`https://portfolio-assistant-rouge.vercel.app`](https://portfolio-assistant-rouge.vercel.app) (ensure backend on Cloud Run isn't cold-sleeping or erroring).
2. [ ] Open LinkedIn on desktop for precise formatting and image upload.
3. [ ] Have the First Comment text copied to your clipboard.

### Moment of Publishing
1. [ ] Paste post copy and verify formatting (ensure empty lines between short paragraphs).
2. [ ] Upload [01_landing_page.png](file:///home/benoi/Projects/Folio_guard/.reports/e2e_screenshots/01_landing_page.png).
3. [ ] Add Alt Text to the image.
4. [ ] Click **Post**.
5. [ ] Immediately post your selected **First Comment** (within 30 seconds).

### First 60 Minutes (Critical Algorithm Window)
1. [ ] Reply to every comment within 10–15 minutes.
2. [ ] Answer technical questions with specific architectural details (e.g., how the XIRR calculation converges or how Kite tokens are encrypted).
3. [ ] Engage with connections who react or share the post.
