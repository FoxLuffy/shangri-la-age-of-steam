---
name: roadmap_implementer
description: Syncs with main, chooses a substantial upgrade from the roadmaps, implements it using TDD, updates documentation, and creates a pull request.
---

# Roadmap Implementer Skill

This skill automates the process of selecting and implementing significant features from the project's roadmaps.

## Workflow Instructions

When the user asks you to implement the next roadmap item, follow this exact sequence:

1. **Sync and Branch:**
   - Run `git checkout main`
   - Run `git pull origin main` (or just `git pull`)
   - Create a new branch: `git checkout -b feature/auto-<feature-name>`

2. **Analyze Roadmaps:**
   - Read `community_roadmap.md` using the `view_file` tool.
   - Choose a suitable, **substantial** upgrade (or a combination of multiple related items). Ensure it has not already been completed.

3. **Test-Driven Design (TDD):**
   - **Write Tests First:** Create or modify tests in `backend/tests/` or frontend test directories that define the expected behavior of the new feature.
   - **Run Tests:** Ensure the tests fail initially (Red).
   - **Implement Feature:** Write the minimal code required to make the tests pass. Ensure backend/frontend integration is solid.
   - **Verify:** Run the tests again to ensure they pass (Green). Refactor if necessary (Refactor).

4. **Update Documentation:**
   - Mark the chosen item(s) as `[x]` in the roadmap files using `replace_file_content`.
   - Update `README.md` if the new feature introduces new environment variables, setup instructions, or architectural changes.

5. **Commit and Pull Request:**
   - Run `git add .`
   - Run `git commit -m "feat: implement <feature-name>"`
   - Push the branch: `git push -u origin feature/auto-<feature-name>`
   - Use the `gh` CLI to create a pull request: `gh pr create --title "feat: <feature-name>" --body "Automated implementation of <feature-name> from the roadmap."`
