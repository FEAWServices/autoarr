# Branch Protection Setup Guide

This guide explains how to configure branch protection rules for the `main` and `develop` branches.

## Why Manual Setup is Needed

Branch protection requires GitHub Admin access with the `repo` scope. While this could be automated via API, it's safer to configure through the GitHub web interface to review settings before applying.

## Setup Instructions

### 1. Navigate to Branch Protection

1. Go to https://github.com/FEAWServices/autoarr/settings/branches
2. Click "Add branch protection rule" or "Add rule"

### 2. Configure `main` Branch Protection

**Branch name pattern:** `main`

**Settings to enable:**

- ✅ **Require a pull request before merging**
  - Required number of approvals: **1**
  - ✅ Dismiss stale pull request approvals when new commits are pushed
  - ✅ Require review from Code Owners (optional)

- ✅ **Require status checks to pass before merging**
  - ✅ Require branches to be up to date before merging
  - **Required status checks** (add these exact names):
    - `Lint & Type Check` (from Python CI)
    - `Test (Python 3.11)` (from Python CI)
    - `Lint & Type Check` (from Frontend CI)
    - `Build & Test` (from Frontend CI)
    - `E2E Tests (Playwright)` (from Frontend CI)

- ✅ **Require conversation resolution before merging**

- ✅ **Require linear history**

- ❌ **Do not allow force pushes**

- ❌ **Do not allow deletions**

- ❌ **Do not require administrators to follow these rules** (allows admin override for emergencies)

### 3. Configure `develop` Branch Protection

**Branch name pattern:** `develop`

**Settings to enable:**

- ✅ **Require status checks to pass before merging**
  - ✅ Require branches to be up to date before merging (optional - less strict for develop)
  - **Required status checks** (add these exact names):
    - `Lint & Type Check` (from Python CI)
    - `Test (Python 3.11)` (from Python CI)
    - `Lint & Type Check` (from Frontend CI)
    - `Build & Test` (from Frontend CI)

- ❌ **Pull request reviews** (optional for develop - allows faster iteration)

- ❌ **Do not allow force pushes**

- ❌ **Do not require administrators to follow these rules** (allows admin override)

## Verifying Check Names

To verify the exact check names from your workflows, run:

```bash
# Get check names from a recent commit
gh api repos/FEAWServices/autoarr/commits/develop/check-runs --jq '.check_runs[] | .name' | sort -u
```

Or view a recent PR's checks in the GitHub UI.

## Alternative: API Setup

If you prefer to use the API, here's the script (requires admin token with `repo` scope):

```bash
# Set up main branch protection
gh api -X PUT repos/FEAWServices/autoarr/branches/main/protection \
  --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "checks": [
      {"context": "Lint & Type Check", "app_id": -1},
      {"context": "Test (Python 3.11)", "app_id": -1},
      {"context": "Build & Test", "app_id": -1},
      {"context": "E2E Tests (Playwright)", "app_id": -1}
    ]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true
}
EOF

# Set up develop branch protection
gh api -X PUT repos/FEAWServices/autoarr/branches/develop/protection \
  --input - <<'EOF'
{
  "required_status_checks": {
    "strict": false,
    "checks": [
      {"context": "Lint & Type Check", "app_id": -1},
      {"context": "Test (Python 3.11)", "app_id": -1},
      {"context": "Build & Test", "app_id": -1}
    ]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF
```

## Testing

After setting up protection:

1. Try to push directly to main: `git push origin main`
   - Should fail with protection error ✅

2. Create a test PR to main
   - Should require status checks to pass ✅
   - Should require 1 approval ✅

3. Create a test PR to develop
   - Should require status checks to pass ✅
   - Should allow merge without approval ✅

## Troubleshooting

**Issue:** Required checks don't appear in the dropdown

**Solution:** The check names must match exactly what appears in GitHub Actions. Run a workflow first, then the check names will appear in the protection rules dropdown.

**Issue:** Can't find the exact check name

**Solution:** Go to a recent PR, click "Checks" tab, and copy the exact name from there.

**Issue:** Checks are failing on old commits

**Solution:** Update branch protection to require checks only for future PRs by not selecting "Require branches to be up to date".

## References

- [GitHub Branch Protection Documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [Git Flow Documentation](./GIT_FLOW.md)
- [CI/CD Workflows](./.github/workflows/)
