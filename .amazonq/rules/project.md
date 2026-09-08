# Portfolio Assistant — Amazon Q Project Rules

## Monorepo Structure
- Backend is at `backend/` — Python 3.10+, FastAPI, Uvicorn
- Frontend is at `frontend/` — Next.js 14 (App Router), TypeScript, Tailwind CSS, Recharts
- Docs are at `docs/` — never move or duplicate them into backend/ or frontend/
- All new backend code goes under `backend/src/`
- All new frontend code goes under `frontend/`

## Active Branch
- All React frontend work is on branch `feature/react-frontend`
- Do not modify `backend/src/ui/app.py` (Streamlit) while building the React frontend

## Version Control Rules

### Branch Strategy
- `main` — stable, production-ready code only. Never commit feature or WIP code directly to main
- `develop` — integration branch. All feature branches merge into develop first
- `feature/<scope>` — new features (e.g. `feature/react-frontend`, `feature/ai-advisory`)
- `fix/<scope>` — bug fixes (e.g. `fix/enctoken-refresh`)
- `chore/<scope>` — non-functional changes (e.g. `chore/update-deps`, `chore/restructure-docs`)

### Automatic Branch Creation
- Before starting any new feature implementation, ALWAYS check the current git branch
- If the current branch is `main` or `develop`, automatically create and switch to a new `feature/<scope>` branch before making any file changes
- Name the branch based on the feature scope being implemented (e.g. `feature/order-staging`, `feature/tax-harvesting`)
- Inform the user which branch was created before proceeding with implementation

### Phase Completion
- When a phase implementation is complete, suggest the exact next branch name to create for the following phase
- Phase-to-branch mapping:
  - Phase 3 (AI Advisory) → `feature/ai-advisory`
  - Phase 4 (Order Staging & Alerts) → `feature/order-staging`
  - Phase 5 (React Frontend) → `feature/react-frontend` (current)
- Remind the user to: squash commits, open a PR into `develop`, and delete the feature branch after merge

### Commit Message Format
- Follow Conventional Commits: `<type>(<scope>): <short description>`
- Types: `feat`, `fix`, `chore`, `docs`, `refactor`, `style`
- Examples:
  - `feat(advisory): add Gemini LLM recommendation endpoint`
  - `fix(enctoken): handle expired token refresh edge case`
  - `chore(deps): upgrade tanstack-query to v5`
  - `docs(readme): update monorepo structure section`
- Keep subject line under 72 characters
- Never commit secrets, tokens, or `.env` files — `.gitignore` must cover these before first commit on any branch

## Backend Rules
- All API routes use prefix `/api/v1/`
- Token is passed as `X-Enctoken` request header
- Never store raw tokens in plaintext — always use environment variables
- All external API calls must use the retry utility at `backend/src/core/retry.py`
- Structured logging via `structlog` with `request_id` propagation on all service calls
- Demo mode is controlled by `DEMO_MODE=true` in `.env` — backend returns demo data transparently

## Frontend Rules
- Use Next.js App Router only — no Pages Router
- Use Tailwind CSS for all styling — no external UI component libraries
- Use Recharts for all charts — no Plotly, no Chart.js
- Use React Query (`@tanstack/react-query`) for all data fetching — no raw useEffect fetches
- Use Axios for HTTP — inject `X-Enctoken` header via interceptor, never hardcode tokens
- TypeScript strict mode — all API response shapes must have types defined in `frontend/lib/types.ts`
- All API call functions live in `frontend/lib/api.ts` only
- All React Query hooks live in `frontend/hooks/usePortfolio.ts`
- Backend API base URL comes from `NEXT_PUBLIC_API_URL` env var, default `http://127.0.0.1:8000`

## Documentation Rules
- When adding any new feature, update the relevant docs in `docs/` before or alongside the implementation — never leave docs stale
- Update `docs/lld/00_INDEX.md` when adding new source files
- Update `docs/architecture/HLD.md` when changing data flow, DB schema, or system boundaries
- Update the relevant `README.md` (root or backend/frontend) when adding new setup steps, env vars, or commands
- Documentation style:
  - Use tables for comparisons, config options, and multi-field data
  - Use bullet points for lists; avoid dense paragraphs
  - Use code blocks with language tags for all code, commands, and env vars
  - Use clear, short headings — prefer `##` and `###`, avoid deep nesting
  - Lead each section with a one-line summary of what it covers
  - Prefer active voice and present tense

## General Rules
- Do not modify `main.py` CORS config during frontend development — CORS is already open for local dev
- Write minimal code — no boilerplate, no unused imports, no placeholder comments
- Do not add tests unless explicitly requested
- Do not add authentication middleware beyond the enctoken header pattern already established
- CORS is already open on the backend for local dev — do not change `main.py` CORS config during frontend development
