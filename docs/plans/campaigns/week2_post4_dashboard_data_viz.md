# FolioGuard — LinkedIn Campaign: Week 2, Post 4 (Dashboard & Data Visualization)

> **Campaign Phase:** Week 2 — AI Engineering & Frontend UX  
> **Post Number:** 4 of 10  
> **Target Day:** Thursday  
> **Ideal Posting Window:** 08:30 AM – 09:30 AM IST (or 06:30 PM – 07:30 PM IST)  
> **Author:** Benoi Rajan  
> **Core Objective:** Showcase institutional-grade frontend engineering, responsive data visualization with Recharts, and clean state/theme architecture in Next.js 14 to attract frontend leads, full-stack engineers, and product-minded hiring managers.  
> **Key Visual Assets:**  
> 1. 2-Slide Carousel: [`02_holdings_tab.png`](file:///home/benoi/Projects/Folio_guard/.reports/e2e_screenshots/02_holdings_tab.png) & [`03_sector_tab.png`](file:///home/benoi/Projects/Folio_guard/.reports/e2e_screenshots/03_sector_tab.png) — Live UI screenshots of the Holdings & Sector Analytics views.  
> 2. AI Image Generation Prompts ([Visual Assets Below](#-visual-assets--image-generation-prompts)).

---

## 📱 Final LinkedIn Post Copy (Ready to Publish)

*(Copy and paste the exact text below into LinkedIn)*

```text
Quantitative analytics are useless if investors can't read the risk at a glance.

Most retail portfolio dashboards dump raw spreadsheets onto a screen — forcing users to hunt for concentration risk, real-time P&L, or sector exposure across cluttered tables.

When designing FolioGuard's frontend in Next.js 14, I aimed for an institutional "Bloomberg Terminal meets Linear" aesthetic: high information density without visual noise.

Here is how we engineered the analytics UI:

1. 📊 6-Card Real-Time KPI Bar (`KpiBar`)
Right at the top of the workspace, investors see Total Invested, Current Value, Overall P&L, Annualized XIRR, Portfolio Beta (vs. NIFTY 50), and SEBI Risk Profile — formatted in Indian locale (`en-IN`) with instant visual polarity.

2. 🍩 Interactive Risk & Allocation Charts (`SectorTab` + Recharts)
Instead of static pie charts, we paired Recharts `ResponsiveContainer` layouts with domain-specific guardrails:
• Sector Allocation Donut Chart for instant exposure breakdown
• Market Cap Distribution Bar Chart (Large / Mid / Small cap tiers)
• Single-Stock Concentration Chart with a live red dashed `ReferenceLine` marking the user's hard concentration cap

3. 🔍 Zero-Friction Holdings Explorer & Ingestion (`HoldingsTab`)
Instant symbol search, multi-select sector filter pills, per-holding weight calculations, and a collapsible CSV/Excel/Zerodha uploader that revalidates portfolio state without page reloads.

4. 🌗 Theme-Aware CSS Variables & SSR Hydration Guards
Built with Tailwind CSS, `next-themes`, and semantic CSS variables (`--surface`, `--border`, `--muted`) so every Recharts tooltip, gridline, and card transitions seamlessly between dark and light modes without hydration flicker.

Good fintech UX isn't about adding more widgets — it's about surfacing the exact threshold where risk turns into action.

What's your go-to charting stack in React/Next.js right now? Recharts, Tremor, ECharts, or custom D3?

Let's compare notes below! 👇

#frontend #nextjs #react #tailwindcss #recharts #datavisualization #uiux #fintech #typescript #buildinpublic
```

---

## 💬 First Comment Templates (Choose One)

> [!TIP]
> **Why post links in the first comment?**  
> LinkedIn’s feed algorithm deprioritizes posts with external outbound links in the caption. Posting the live app and repo in the first comment ensures maximum reach.

### Option 1: Component Walkthrough & Live Demo (Recommended)
```text
Want to explore the live dashboard and switch between dark/light modes?

🌐 Live App Demo: https://portfolio-assistant-rouge.vercel.app
💻 GitHub Repository: https://github.com/benoirajan/portfolio-assistant

Key Frontend Files to Inspect:
• 6-Card KPI Summary: `frontend/components/kpi/KpiBar.tsx`
• Recharts Risk & Sector Visuals: `frontend/components/tabs/SectorTab.tsx`
• Holdings Table & CSV/Excel Uploader: `frontend/components/tabs/HoldingsTab.tsx`
• SSR-Safe Theme Provider: `frontend/components/theme/ThemeProvider.tsx`

Happy to share how we wired the custom CSS variables into Recharts tooltips and reference lines!
```

### Option 2: Design System & Charting Focus
```text
🌐 Try the interactive dashboard here: https://portfolio-assistant-rouge.vercel.app

Every chart in FolioGuard uses semantic CSS variables (`var(--surface)`, `var(--border)`, `var(--blue)`, `var(--red)`) so Recharts components stay 100% theme-aware across dark and light modes.

Drop a comment if you're building financial dashboards in Next.js — would love to see what charting libraries you've had the best experience with!
```

---

## 🎨 Visual Assets & Image Generation Prompts

You can post the 2-slide live product carousel ([02_holdings_tab.png](file:///home/benoi/Projects/Folio_guard/.reports/e2e_screenshots/02_holdings_tab.png) + [03_sector_tab.png](file:///home/benoi/Projects/Folio_guard/.reports/e2e_screenshots/03_sector_tab.png)), or generate a custom hero visual using the prompts below.

### Option A: Live Product Carousel (Ready to Upload — Recommended)
* **Slide 1:** [`02_holdings_tab.png`](file:///home/benoi/Projects/Folio_guard/.reports/e2e_screenshots/02_holdings_tab.png)
  * **Alt Text:** `FolioGuard Holdings dashboard showing the 6-card KPI summary bar, sector filter pills, symbol search, and live Indian equity holdings table`
* **Slide 2:** [`03_sector_tab.png`](file:///home/benoi/Projects/Folio_guard/.reports/e2e_screenshots/03_sector_tab.png)
  * **Alt Text:** `FolioGuard Sector Analytics view featuring a Recharts sector allocation donut chart, market cap bar chart, and single-stock concentration chart with threshold reference line`

---

### Option B: AI Image Generation Prompts (Midjourney / DALL-E 3 / Imagen 3)

#### Prompt 1: Institutional Dark-Mode Fintech Dashboard Showcase (Recommended)
```text
An ultra-clean, angled 3D perspective showcase of a modern dark-mode institutional fintech web dashboard floating over a deep obsidian slate background (#0B1120). The interface features a crisp top KPI strip with glowing emerald green and electric blue metrics, a luminous multi-segment donut chart for sector allocation, a sleek market-cap bar chart, and a single-stock concentration bar chart crossed by a sharp glowing red horizontal threshold line. Minimalist Linear-meets-Bloomberg aesthetic, subtle glassmorphism cards, razor-sharp UI typography, soft volumetric rim lighting, 8k resolution --ar 16:9
```

#### Prompt 2: Dark Mode vs. Light Mode Split-Screen UI Concept
```text
A high-contrast split-screen architectural product render of a modern financial analytics dashboard, seamlessly divided diagonally between deep obsidian dark mode on the left and crisp alabaster light mode on the right. Both halves display synchronized Recharts-style donut charts, bar graphs, and clean portfolio KPI cards with glowing blue and emerald accents. Studio product photography style, ultra-sharp vector UI clarity, minimalist SaaS design showcase, 8k --ar 1200:627
```

#### Prompt 3: Data Visualization & Risk Threshold Abstract Graphic
```text
A minimalist 3D technical illustration of glowing financial data bars and concentric allocation rings emerging from a sleek dark glass tablet. Electric blue and cyan bars rise cleanly from a subtle grid, while one oversized bar is intersected by a sharp, glowing crimson laser threshold line representing portfolio concentration risk limits. Obsidian background, subtle depth of field, octane render, modern fintech engineering aesthetic, 8k --ar 16:9
```

---

## 🔄 Alternative Hooks (For Reference / Future Iteration)

### Option B — The "Charting Guardrails" Hook
> *"A pie chart tells you what you own. A bar chart with a hard red threshold line tells you when you're over-exposed. Here is how we built actionable risk visuals in FolioGuard using Next.js 14 and Recharts."*

### Option C — The "Dark/Light Mode in Recharts" Hook
> *"The hardest part of building dark/light mode in a React analytics app isn't the Tailwind cards — it's making third-party chart tooltips, axes, and gridlines adapt without hydration flicker. Here is the CSS variable pattern we used in FolioGuard."*

---

## ⏱️ Pre-Publishing & Post-Publishing Protocol

### 15 Minutes Before Publishing
1. [ ] Verify [`https://portfolio-assistant-rouge.vercel.app`](https://portfolio-assistant-rouge.vercel.app) loads cleanly and the Holdings & Sector tabs render without layout shift.
2. [ ] Have your chosen First Comment copied to your clipboard.

### Moment of Publishing
1. [ ] Paste the post copy and verify line breaks on LinkedIn desktop preview.
2. [ ] Attach the 2-slide carousel ([02_holdings_tab.png](file:///home/benoi/Projects/Folio_guard/.reports/e2e_screenshots/02_holdings_tab.png) and [03_sector_tab.png](file:///home/benoi/Projects/Folio_guard/.reports/e2e_screenshots/03_sector_tab.png)) or your generated hero graphic, and add Alt Text.
3. [ ] Click **Post** and immediately drop the **First Comment** within 30 seconds.

### First 60 Minutes (Critical Algorithm Window)
1. [ ] Reply promptly to questions about Recharts responsiveness, Tailwind theming, or Next.js 14 App Router state management.
