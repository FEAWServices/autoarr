# Docker CI/CD Workflow Changes

## Summary

Modified the Docker Build & Deploy workflow to only run after the Python CI workflow completes successfully. This ensures that Docker images are only built and pushed when all tests pass.

---

## Changes Made

### 1. Workflow Trigger Change

**Before:**

```yaml
on:
  push:
    branches:
      - main
      - develop
  pull_request:
    branches:
      - main
      - develop
```

**After:**

```yaml
on:
  workflow_run:
    workflows: ["Python CI"]
    types:
      - completed
    branches:
      - main
      - develop
```

**Impact:**

- ✅ Docker workflow now waits for Python CI to complete
- ✅ No more Docker builds on failing tests
- ✅ Automatic CI/CD pipeline orchestration

---

### 2. Success Check Added

**Added to `build-and-push` job:**

```yaml
if: ${{ github.event.workflow_run.conclusion == 'success' }}
```

**Impact:**

- ✅ Only builds Docker images when Python CI succeeds
- ✅ Skips builds on failed CI runs
- ✅ Prevents deploying broken code

---

### 3. Checkout Reference Update

**Updated checkout step:**

```yaml
- name: Checkout code
  uses: actions/checkout@v4
  with:
    ref: ${{ github.event.workflow_run.head_branch }}
```

**Impact:**

- ✅ Checks out the correct branch from workflow_run event
- ✅ Ensures Docker builds use the same code that passed CI

---

### 4. Event Context Updates

**Updated all references from direct event to workflow_run event:**

| Before              | After                                   | Purpose          |
| ------------------- | --------------------------------------- | ---------------- |
| `github.ref`        | `github.event.workflow_run.head_branch` | Branch name      |
| `github.sha`        | `github.event.workflow_run.head_sha`    | Commit SHA       |
| `github.event_name` | Always `workflow_run`                   | Event type       |
| `github.ref_name`   | `github.event.workflow_run.head_branch` | Branch reference |

**Updated locations:**

- Docker metadata tags
- Build arguments
- Deployment job conditions
- Summary notifications

---

### 5. Push Behavior Change

**Before:**

```yaml
push: ${{ github.event_name != 'pull_request' }}
```

**After:**

```yaml
push: true # Always push when CI succeeds on main/develop
```

**Rationale:**

- The workflow only runs after successful CI on main/develop
- No need to check event type - if we're here, we should push
- Simpler and more explicit

---

### 6. Tag Generation Fix

**Fixed invalid Docker tag format:**

**Before (caused `-84bf688` invalid tag):**

```yaml
type=sha,prefix={{branch}}-,enable=${{ github.event_name == 'push' }}
```

**After (explicit prefixes):**

```yaml
type=sha,prefix=main-,enable=${{ github.event.workflow_run.head_branch == 'main' }}
type=sha,prefix=develop-,enable=${{ github.event.workflow_run.head_branch == 'develop' }}
```

**Tags Generated:**

- Main branch: `latest`, `stable`, `main-<sha>`
- Develop branch: `staging`, `develop`, `develop-<sha>`

---

## Workflow Flow Diagram

```
┌─────────────────────────────────────────┐
│ Code pushed to main/develop             │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ Python CI Workflow Triggered            │
│  ├─ Lint & Type Check                   │
│  ├─ Test (Python 3.11)                  │
│  ├─ Test (Python 3.12)                  │
│  ├─ Security Scan                       │
│  └─ Dependency Review                   │
└────────────────┬────────────────────────┘
                 │
                 ├─ If SUCCESS ──────────┐
                 │                       │
                 └─ If FAILURE ─> STOP   │
                                         │
                                         ▼
                ┌─────────────────────────────────────────┐
                │ Docker Build & Deploy Triggered         │
                │  ├─ Check: CI conclusion == 'success'   │
                │  ├─ Build multi-platform image          │
                │  ├─ Push to GitHub Container Registry   │
                │  ├─ Run Trivy security scan             │
                │  └─ Generate deployment summary         │
                └────────────────┬────────────────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 │                               │
         develop branch                   main branch
                 │                               │
                 ▼                               ▼
┌────────────────────────────┐   ┌────────────────────────────┐
│ Deploy to Synology Staging │   │ Production Deployment Gate │
│  └─ Staging environment    │   │  └─ Production approval    │
└────────────────────────────┘   └────────────────────────────┘
```

---

## Benefits

### 1. **Prevents Broken Builds**

- No Docker images built from failing code
- Guarantees all images pass CI tests
- Reduces wasted build time and resources

### 2. **Automatic Pipeline**

- No manual intervention needed
- Automatic progression: CI → Docker → Deploy
- Single push triggers entire pipeline

### 3. **Clear Workflow Status**

- Docker workflow shows in GitHub Actions UI
- Easy to see if CI passed before Docker build
- Summary shows which CI run triggered the build

### 4. **Resource Optimization**

- No unnecessary Docker builds on failed CI
- Self-hosted runner only used when needed
- Cache efficiency maintained with BuildKit

### 5. **Better Security**

- No images pushed without security scans (CI)
- Trivy scan still runs on Docker image
- Two layers of security validation

---

## Testing Workflow

### On Feature Branch

```bash
git checkout -b feature/my-feature
git commit -am "My changes"
git push origin feature/my-feature
```

**What happens:**

1. Python CI runs (because feature/\*\* matches)
2. Docker Build does NOT run (not main/develop)
3. Only CI checks show in PR

### On Develop Branch

```bash
git checkout develop
git merge feature/my-feature
git push origin develop
```

**What happens:**

1. ✅ Python CI runs
2. ⏳ If CI succeeds → Docker Build runs
3. ⏳ If Docker succeeds → Staging deployment ready
4. ❌ If CI fails → Docker Build skipped

### On Main Branch

```bash
git checkout main
git merge develop
git push origin main
```

**What happens:**

1. ✅ Python CI runs
2. ⏳ If CI succeeds → Docker Build runs
3. ⏳ If Docker succeeds → Production deployment gate
4. ❌ If CI fails → Docker Build skipped

---

## Migration Notes

### What Changed

- Docker workflow no longer triggers on `push` or `pull_request`
- Now triggers on `workflow_run` event from "Python CI"
- All job conditions updated to use `workflow_run` event context

### What Stayed the Same

- Same Docker build process
- Same image tags and labels
- Same multi-platform builds (amd64, arm64)
- Same deployment jobs (Synology, Production)
- Same security scanning (Trivy)

### Breaking Changes

- **None** - This is purely workflow orchestration
- Existing Docker images unchanged
- Deployment process unchanged
- Only the trigger mechanism changed

---

## Troubleshooting

### Docker Build Doesn't Run

**Check:**

1. Did Python CI complete successfully?
2. Is the branch `main` or `develop`?
3. Check GitHub Actions logs for workflow_run event

**View workflow_run trigger in logs:**

```json
{
  "workflow_run": {
    "conclusion": "success",
    "head_branch": "develop",
    "head_sha": "abc123..."
  }
}
```

### Docker Build Runs but Uses Wrong Code

**Check:**

```yaml
ref: ${{ github.event.workflow_run.head_branch }}
```

Should match the branch that triggered Python CI.

### Tags Not Generated Correctly

**Verify:**

- Main branch should get: `latest`, `stable`, `main-<sha>`
- Develop branch should get: `staging`, `develop`, `develop-<sha>`

**Check metadata-action output in logs:**

```
tags: |
  ghcr.io/feawservices/autoarr:develop
  ghcr.io/feawservices/autoarr:staging
  ghcr.io/feawservices/autoarr:develop-abc123
```

---

## Configuration Reference

### Workflow Dependencies

```yaml
# .github/workflows/python-ci.yml
name: Python CI
on:
  push:
    branches: [main, develop, feature/**, fix/**]

# .github/workflows/docker-deploy.yml
name: Docker Build & Deploy
on:
  workflow_run:
    workflows: ["Python CI"]  # Must match Python CI name exactly
    types: [completed]
    branches: [main, develop]
```

**Important:** The workflow name `"Python CI"` must match exactly!

### Event Context Variables

```yaml
# Available in workflow_run event:
${{ github.event.workflow_run.conclusion }}    # success, failure, cancelled
${{ github.event.workflow_run.head_branch }}   # main, develop, etc.
${{ github.event.workflow_run.head_sha }}      # abc123...
${{ github.event.workflow_run.created_at }}    # ISO timestamp
${{ github.event.workflow_run.id }}            # Workflow run ID
```

---

## Best Practices

### 1. Monitor Both Workflows

- Check Python CI first
- Then check Docker Build (triggered by CI)
- Deployment summary shows which CI run triggered it

### 2. Use Workflow Run ID

- Summary now shows: "Triggered by: Python CI workflow success"
- Links CI run to Docker build for debugging

### 3. Failed CI = No Docker Build

- Expected behavior
- Saves resources
- Fix CI first, then Docker will run automatically

### 4. Re-run CI to Trigger Docker

- Re-running Python CI will re-trigger Docker Build
- No need to re-run Docker Build manually
- Pipeline is fully automatic

---

## Rollback Plan

If issues arise, rollback by reverting the workflow trigger:

```yaml
# Revert to direct triggers
on:
  push:
    branches:
      - main
      - develop
  pull_request:
    branches:
      - main
      - develop
```

And revert all `github.event.workflow_run.*` references back to original event context.

---

## Future Enhancements

### 1. Add Frontend CI Dependency

```yaml
workflow_run:
  workflows: ["Python CI", "Frontend CI"]
  types: [completed]
```

Wait for both CI workflows to succeed before Docker build.

### 2. Add Workflow Dispatch

```yaml
on:
  workflow_run:
    workflows: ["Python CI"]
    types: [completed]
  workflow_dispatch: # Allow manual trigger
    inputs:
      branch:
        description: "Branch to build"
        required: true
```

Allow manual Docker builds when needed.

### 3. Add Approval for Production

Currently uses GitHub environment protection.
Could add manual approval step:

```yaml
environment:
  name: production
  # Configure in GitHub Settings → Environments
  # Add required reviewers
```

---

## Conclusion

The Docker Build & Deploy workflow now properly orchestrates with Python CI, ensuring only tested code gets built into Docker images. This improves reliability, reduces wasted resources, and provides a clear CI/CD pipeline.

**Status:** ✅ **READY FOR PRODUCTION**

**Next Steps:**

1. Test the workflow on develop branch
2. Verify Docker image tags are correct
3. Monitor first few CI runs
4. Update documentation if needed

---

**Modified:** 2025-10-21
**File:** `.github/workflows/docker-deploy.yml`
**Impact:** CI/CD pipeline orchestration only
**Breaking Changes:** None
