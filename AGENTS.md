# Agent Guidelines & Repository Rules

## Mandatory Post-Task Documentation & Task Cleanup Policy

For all conversations and agent tasks in this repository, the following protocol must be strictly adhered to upon finishing any task, bug fix, or feature:

### 1. Document Completed Tasks in `docs/`
- Every completed task must be documented in `docs/plans/completed_tasks.md` with:
  - Task title and priority
  - Architectural rationale and objective
  - Concrete implementation details (files, classes, routes)
  - Verification results and test status
- If the task added or altered architecture, schemas, or endpoints, update or create the relevant low-level design document in `docs/lld/` and register it in `docs/lld/00_INDEX.md`.

### 2. Remove Completed Items from Active Task Lists
- Immediately remove completed tasks from `docs/plans/todo_tomorrow_tasks.md`.
- `docs/plans/todo_tomorrow_tasks.md` must only contain active, pending, uncompleted work.
- It must maintain a top-level link to `docs/plans/completed_tasks.md` for historical traceability.
