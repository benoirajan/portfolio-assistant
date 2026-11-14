---
trigger: always_on
description: Mandatory post-task documentation update and TODO cleanup rule
globs: "**/*"
---

# Mandatory Post-Task Documentation & Task Cleanup Rule

For all tasks in this repository, follow this mandatory workflow upon completing any task, feature implementation, or bug fix:

## 1. Document Completed Work in `docs/`
- **Update Technical Specs / LLD**: If the task adds or modifies models, APIs, architecture, or design patterns, update or create the relevant document in `docs/lld/` (or `docs/architecture/`) and register it in `docs/lld/00_INDEX.md`.
- **Sync Agent Skills**: If the task affects agent workflows, update relevant `.agents/skills/` documentation.
