# Agent Guidelines & Repository Rules

## Mandatory Post-Task Documentation & Task Cleanup Policy

For all conversations and agent tasks in this repository, the following protocol must be strictly adhered to upon finishing any task, bug fix, or feature:

### 1. Architectural & Design Documentation in `docs/`
- If the task added or altered architecture, schemas, or endpoints, update or create the relevant low-level design document in `docs/lld/` and register it in `docs/lld/00_INDEX.md`.

### 2. Manage Tasks & Issues via GitHub Issues
- Tasks, backlogs, and completion tracking are managed directly via GitHub Issues ([Issues Tracker](https://github.com/benoirajan/portfolio-assistant/issues)).
- When finishing a task that has a corresponding GitHub issue, close or comment on the issue with the completion summary (including architectural rationale, implementation details, and verification results).

### 3. Security & Sensitive File Policy
- **Strictly Disallowed**: NEVER read, view, print, grep, or edit any `.env` or `.env.*` files.
- If environment variables or configurations are needed, refer strictly to `.env.example` or prompt the user for variable keys.
