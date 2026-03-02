# Release Process

This repo uses Semantic Versioning and tags releases in git.

## Steps
1. Update `CHANGELOG.md`:
   - Move items from **[Unreleased]** into a new version section.
   - Add the release date in YYYY-MM-DD format.
2. Commit the changelog:
   - `git add CHANGELOG.md`
   - `git commit -m "chore(release): vX.Y.Z"`
3. Create the git tag:
   - `git tag vX.Y.Z`
4. Push commit and tag:
   - `git push`
   - `git push --tags`

## Versioning rules (SemVer)
- **MAJOR**: incompatible API changes.
- **MINOR**: backward-compatible features.
- **PATCH**: backward-compatible bug fixes.
