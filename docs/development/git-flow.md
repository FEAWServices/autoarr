# Git Flow & Branching Strategy

## Overview

AutoArr uses a simplified Git Flow branching strategy to maintain two environments:

- **`develop`** - Staging environment (daily latest builds)
- **`main`** - Production environment (stable releases)

## Branch Structure

```
main (production) ─────●────────●────────●─────> latest stable release
                        │        │        │
                        │        │        │
develop (staging) ─●───●────●───●────●───●─────> daily latest
                    │   │    │   │    │   │
                    │   │    │   │    │   │
feature branches ───●───●    │   │    ●───●
                             │   │
fix branches ────────────────●───●
```

## Branching Model

### Main Branches

#### 1. `main` - Production

- **Purpose**: Stable, production-ready code
- **Deployment**: Automatically builds Docker images tagged as `latest` and `stable`
- **Protection**: Requires PR approval, passing CI tests
- **Release**: Only merge from `develop` after thorough testing

#### 2. `develop` - Staging

- **Purpose**: Integration branch for daily development
- **Deployment**: Automatically builds Docker images tagged as `staging` and `develop`
- **Protection**: Requires passing CI tests
- **Updates**: Daily merges from feature branches

### Supporting Branches

#### Feature Branches

- **Naming**: `feature/<sprint-number>-<description>` or `feature/<description>`
- **Branch from**: `develop`
- **Merge to**: `develop`
- **Examples**:
  - `feature/sprint-11-advanced-monitoring`
  - `feature/llm-caching-optimization`
  - `feature/ui-dark-mode`

#### Fix Branches

- **Naming**: `fix/<issue-number>-<description>` or `fix/<description>`
- **Branch from**: `develop` (or `main` for hotfixes)
- **Merge to**: `develop` (or both `develop` and `main` for hotfixes)
- **Examples**:
  - `fix/123-sabnzbd-timeout`
  - `fix/authentication-bug`

#### Hotfix Branches

- **Naming**: `hotfix/<version>-<description>`
- **Branch from**: `main`
- **Merge to**: Both `main` and `develop`
- **Purpose**: Critical production fixes
- **Example**: `hotfix/1.0.1-security-patch`

## Workflow

### 1. Daily Development (Feature Work)

```bash
# Start new feature
git checkout develop
git pull origin develop
git checkout -b feature/my-new-feature

# Work on feature
git add .
git commit -m "feat: implement new feature"
git push origin feature/my-new-feature

# Create PR to develop
gh pr create --base develop --title "feat: My New Feature" --body "Description..."

# After PR approval and CI passes
# Merge to develop (staging deployment happens automatically)
```

### 2. Production Release

```bash
# When develop is stable and ready for production
git checkout develop
git pull origin develop

# Create release PR from develop to main
gh pr create --base main --head develop --title "Release v1.1.0" --body "
## Changes in this release
- Feature A
- Feature B
- Bug fix C

## Testing
- [x] All CI tests passing
- [x] Staging environment tested
- [x] Manual QA completed
"

# After PR approval
# Merge to main (production deployment happens automatically)

# Tag the release
git checkout main
git pull origin main
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin v1.1.0
```

### 3. Hotfix (Emergency Production Fix)

```bash
# Start hotfix from main
git checkout main
git pull origin main
git checkout -b hotfix/1.0.1-critical-bug

# Fix the bug
git add .
git commit -m "fix: critical bug in production"
git push origin hotfix/1.0.1-critical-bug

# Create PR to main
gh pr create --base main --title "hotfix: Critical Bug Fix v1.0.1"

# After merge to main, also merge to develop
git checkout develop
git pull origin develop
git merge main
git push origin develop
```

## CI/CD Pipeline

### Automated Workflows

#### On Push to `develop` (Staging)

1. **Python CI**: Linting, type checking, unit tests, security scans
2. **Frontend CI**: ESLint, Prettier, TypeScript, Playwright tests
3. **Docker Build**: Build multi-platform image, tag as `staging` and `develop`
4. **Push to GHCR**: Publish to GitHub Container Registry
5. **Staging Notification**: Ready for Synology NAS deployment

#### On Push to `main` (Production)

1. **Python CI**: Full test suite with integration tests
2. **Frontend CI**: Full E2E and accessibility tests
3. **Docker Build**: Build multi-platform image, tag as `latest` and `stable`
4. **Security Scan**: Trivy vulnerability scanning
5. **Push to GHCR**: Publish production image
6. **Production Gate**: Manual deployment step

#### On Pull Requests

1. Run all CI tests
2. Require passing status checks
3. Bundle size analysis (frontend)
4. Dependency review
5. Security scanning

## Docker Image Tags

| Branch         | Tags                                  | Purpose                           |
| -------------- | ------------------------------------- | --------------------------------- |
| `develop`      | `staging`, `develop`, `develop-<sha>` | Latest staging builds for testing |
| `main`         | `latest`, `stable`, `main-<sha>`      | Production-ready releases         |
| Tagged release | `v1.0.0`, `1.0`, `1`                  | Semantic versioned releases       |

## Pull Request Guidelines

### PR Titles (Conventional Commits)

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `chore:` - Maintenance tasks
- `test:` - Test additions/changes
- `refactor:` - Code refactoring
- `perf:` - Performance improvements
- `ci:` - CI/CD changes

### PR Template

```markdown
## Description

Brief description of changes

## Type of Change

- [ ] Feature (new functionality)
- [ ] Bug fix (fixes an issue)
- [ ] Breaking change (requires version bump)
- [ ] Documentation update

## Testing

- [ ] Unit tests added/updated
- [ ] Integration tests passing
- [ ] E2E tests passing
- [ ] Manual testing completed

## Checklist

- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings or errors
- [ ] Tests provide adequate coverage
```

## Branch Protection Rules

### `main` Branch

- ✅ Require PR reviews (1 approval minimum)
- ✅ Require status checks to pass:
  - `Python CI / lint`
  - `Python CI / test`
  - `Frontend CI / lint`
  - `Frontend CI / build`
  - `Frontend CI / e2e`
- ✅ Require conversation resolution
- ✅ Require linear history (squash merges)
- ✅ Do not allow force pushes
- ✅ Do not allow deletions

### `develop` Branch

- ✅ Require status checks to pass:
  - `Python CI / lint`
  - `Python CI / test`
  - `Frontend CI / lint`
  - `Frontend CI / build`
- ⚠️ Allow squash and merge commits
- ✅ Do not allow force pushes

## Deployment Strategy

### Staging Deployment (`develop` → Synology NAS Staging)

```bash
# Automatic on push to develop
# Pull latest staging image
docker pull ghcr.io/feawservices/autoarr:staging

# Update staging environment
cd /volume1/docker/autoarr-staging
docker-compose pull
docker-compose up -d
```

### Production Deployment (`main` → Synology NAS Production)

```bash
# Manual after reviewing staging
# Pull production image
docker pull ghcr.io/feawservices/autoarr:latest

# Update production environment
cd /volume1/docker/autoarr
docker-compose pull
docker-compose up -d

# Verify deployment
docker logs autoarr --tail 100
curl http://localhost:8088/health
```

## Version Numbering

AutoArr follows [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.x.x): Breaking changes, incompatible API changes
- **MINOR** (x.1.x): New features, backwards-compatible
- **PATCH** (x.x.1): Bug fixes, backwards-compatible

### Release Process

1. Update version in `pyproject.toml` and `package.json`
2. Update `CHANGELOG.md` with release notes
3. Merge `develop` → `main` via PR
4. Tag release: `git tag -a v1.1.0 -m "Release v1.1.0"`
5. Push tag: `git push origin v1.1.0`
6. GitHub Actions builds and publishes Docker image
7. Create GitHub Release with changelog

## Common Workflows

### Starting a New Sprint

```bash
git checkout develop
git pull origin develop
git checkout -b feature/sprint-11-advanced-monitoring
```

### Updating Feature Branch with Latest `develop`

```bash
git checkout feature/my-feature
git fetch origin
git rebase origin/develop
# Resolve conflicts if any
git push --force-with-lease
```

### Cleaning Up Merged Branches

```bash
# Delete local feature branch after merge
git branch -d feature/my-feature

# Delete remote feature branch (auto-deleted by GitHub PR merge)
git push origin --delete feature/my-feature

# Clean up local references
git fetch --prune
```

## Best Practices

1. **Commit Often**: Make small, focused commits
2. **Write Good Messages**: Follow Conventional Commits format
3. **Keep PRs Small**: Easier to review and merge
4. **Test Locally**: Run `poetry run test` before pushing
5. **Use Pre-commit Hooks**: `poetry run pre-commit install`
6. **Rebase Feature Branches**: Keep commit history clean
7. **Squash Merge**: Use squash when merging to `develop` or `main`
8. **Tag Releases**: Always tag production releases
9. **Document Changes**: Update docs with new features
10. **Review Staging**: Test in staging before production release

## Troubleshooting

### PR Checks Failing

```bash
# Run tests locally
poetry run test

# Run linters
poetry run black autoarr/
poetry run flake8 autoarr/

# Frontend checks
cd autoarr/ui
pnpm run lint
pnpm exec prettier --check "src/**/*.{ts,tsx,css}"
pnpm exec tsc --noEmit
```

### Merge Conflicts

```bash
# Update feature branch
git checkout feature/my-feature
git fetch origin
git rebase origin/develop

# Resolve conflicts in files
# Then continue rebase
git add .
git rebase --continue
```

### Accidentally Committed to Wrong Branch

```bash
# If not pushed yet
git reset HEAD~1
git stash
git checkout correct-branch
git stash pop

# If already pushed (create new branch)
git checkout -b correct-branch
git push origin correct-branch
```

## References

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [Git Flow (original)](https://nvie.com/posts/a-successful-git-branching-model/)

---

_For questions or improvements to this workflow, please open an issue._
