---
description: Mandatory post-task documentation update and TODO cleanup rule
globs: ["**/*"]
---

# Mandatory Post-Task Documentation & Task Cleanup Rule

For all tasks in this repository, follow this mandatory workflow upon completing any task, feature implementation, or bug fix:

## 1. Document Completed Work in `docs/`
- **Archive in Completed Tasks**: Immediately document the completed task with its architectural rationale, implementation details, files modified, and test verification in [docs/plans/completed_tasks.md](file:///home/benoi/Projects/portfolio_assistant/docs/plans/completed_tasks.md).
- **Update Technical Specs / LLD**: If the task adds or modifies models, APIs, architecture, or design patterns, update or create the relevant document in `docs/lld/` (or `docs/architecture/`) and register it in `docs/lld/00_INDEX.md`.
- **Sync Agent Skills**: If the task affects agent workflows, update relevant `.agents/skills/` documentation.

## 2. Prune Completed Items from Active TODO Lists
- Remove completed items from [docs/plans/todo_tomorrow_tasks.md](file:///home/benoi/Projects/portfolio_assistant/docs/plans/todo_tomorrow_tasks.md).
- The active TODO list must strictly contain **only pending / upcoming items**.
- Maintain the link at the top of `todo_tomorrow_tasks.md` pointing to `completed_tasks.md`.

## 3. Strict Rule Adherence
- Never leave finished tasks sitting in `todo_tomorrow_tasks.md` as completed checkmarks. Move them immediately to the documentation archive upon completion.
