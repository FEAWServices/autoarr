# Security Scanning & Supply Chain Security

This document explains AutoArr's comprehensive security scanning setup for public GPL release.

## Overview

AutoArr implements **multiple layers of security scanning** across different stages of the development and release lifecycle:

1. **Static Application Security Testing (SAST)** - CI pipeline
2. **Dependency Vulnerability Scanning** - CI pipeline
3. **Container Image Scanning** - Release workflow
4. **SBOM Generation** - Release workflow
5. **Code Quality Analysis** - SonarCloud & CodeQL
6. **Supply Chain Security** - SLSA provenance

---

## Security Scanning During CI (Pre-Release)

### 1. Python Security Scanning

**Workflow:** `.github/workflows/ci.yml` → `python-security` job

**Tools:**

- **Bandit** - Python security linter (PyCQA)
- **Safety** - Dependency vulnerability checker

**What It Scans:**

- Python source code for common security issues:
  - SQL injection vulnerabilities
  - Hardcoded secrets
  - Insecure cryptography
  - Command injection risks
  - Unsafe YAML loading
- Python dependencies (via `poetry.lock`) for known CVEs

**Execution:**

```bash
# Run locally
poetry run bandit -r autoarr/ -f json -o bandit-report.json
poetry run safety check --json
```

**Failure Policy:**

- HIGH severity issues → Build fails ❌
- MEDIUM severity → Warning only ⚠️
- Results uploaded to GitHub Security tab

---

### 2. CodeQL Analysis

**Workflow:** `.github/workflows/codeql.yml`

**Language:** Python

**What It Scans:**

- Security vulnerabilities (CWE patterns)
- Code injection vulnerabilities
- Path traversal issues
- Authentication/authorization flaws
- Cryptographic weaknesses

**Query Sets:**

- Default security queries
- Can be extended with `security-extended` or `security-and-quality`

**Results:**

- Available in GitHub Security → Code scanning alerts
- Integrates with pull request reviews

---

### 3. SonarCloud (Code Quality + Security)

**Workflow:** `.github/workflows/ci.yml` → `sonarcloud` job

**What It Analyzes:**

- Code smells and bugs
- Security hotspots
- Test coverage
- Code duplication
- Maintainability rating

**Dashboard:** https://sonarcloud.io/project/overview?id=YOUR_PROJECT_KEY

---

## Security Scanning During Release

### 1. Trivy Container Scanning

**Workflow:** `.github/workflows/release-please.yml` → `docker-release` job

**Tool:** Aqua Security Trivy (industry-standard container scanner)

**What It Scans:**

- **OS packages** (Alpine Linux base)
- **Application dependencies** (Python packages)
- **Known CVEs** from multiple databases:
  - NVD (National Vulnerability Database)
  - Red Hat Security Data
  - Debian Security Tracker
  - Alpine SecDB
  - GitHub Security Advisories

**Severity Levels:**

- **CRITICAL** - Immediate action required, build fails
- **HIGH** - Build fails, must be fixed before release
- **MEDIUM** - Warning, reviewed before release
- **LOW** - Informational

**Configuration:**

```yaml
- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ghcr.io/${{ github.repository }}:${{ version }}
    format: "sarif"
    output: "trivy-results.sarif"
    severity: "CRITICAL,HIGH"
  continue-on-error: false # Build fails on HIGH/CRITICAL
```

**Outputs:**

1. **SARIF format** → Uploaded to GitHub Security tab
2. **Table format** → Attached to GitHub release as `security-scan-X.Y.Z.txt`

**Failure Policy:**

- CRITICAL or HIGH vulnerabilities → **Release blocked** ❌
- Build will not complete until vulnerabilities are resolved

---

### 2. SBOM Generation (Software Bill of Materials)

**Workflow:** `.github/workflows/release-please.yml` → `docker-release` job

**Standard:** SPDX (Software Package Data Exchange)

**What It Includes:**

- Complete list of all packages in the container image
- Package versions and licenses
- Dependencies and relationships
- Provenance information

**Configuration:**

```yaml
- name: Build and push
  uses: docker/build-push-action@v6
  with:
    sbom: true # Generate SBOM
    provenance: true # SLSA provenance
```

**Access:**

- Automatically attached to Docker images in both GHCR and Docker Hub
- Can be inspected with:
  ```bash
  docker buildx imagetools inspect ghcr.io/feawservices/autoarr:latest --format '{{json .SBOM}}'
  ```

**Use Cases:**

- Supply chain security audits
- License compliance verification
- Vulnerability tracking
- Incident response

---

### 3. SLSA Provenance

**Standard:** SLSA Level 3 (Supply-chain Levels for Software Artifacts)

**What It Provides:**

- Build environment attestation
- Source code commit hash
- Builder identity
- Build parameters
- Cryptographic signature

**Benefits:**

- Verifiable build integrity
- Tamper detection
- Supply chain attack prevention
- Compliance requirements (NIST, CISA)

**Verification:**

```bash
# Verify provenance
docker buildx imagetools inspect ghcr.io/feawservices/autoarr:latest --format '{{json .Provenance}}'
```

---

## Security Artifacts in Releases

Each GitHub release includes the following security artifacts:

### 1. Security Scan Report

**File:** `security-scan-X.Y.Z.txt`

**Contents:**

- Complete Trivy vulnerability scan results
- List of all detected vulnerabilities
- Severity ratings
- Affected packages and versions
- Remediation recommendations

**Example:**

```
Total: 0 (CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0)
┌───────────────┬──────────────┬──────────┬─────────────────┬───────────────┬────────────────────────┐
│    Library    │ Vulnerability│ Severity │ Installed Version│ Fixed Version │         Title          │
├───────────────┼──────────────┼──────────┼─────────────────┼───────────────┼────────────────────────┤
│ No vulnerabilities found                                                                          │
└───────────────┴──────────────┴──────────┴─────────────────┴───────────────┴────────────────────────┘
```

### 2. SHA256 Checksums

**File:** `SHA256SUMS.txt`

**Contents:**

- Checksums for all release assets
- Native executables (Linux, Windows, macOS)
- Can verify with: `sha256sum -c SHA256SUMS.txt`

### 3. SBOM (Attached to Docker Image)

**Access:** Via Docker image inspection

**Use:**

```bash
docker buildx imagetools inspect ghcr.io/feawservices/autoarr:X.Y.Z
```

---

## Monitoring & Alerts

### GitHub Security Tab

All security scan results are centralized in:
**Repository → Security → Code scanning alerts**

**Contains:**

- CodeQL findings
- Trivy vulnerability reports
- Dependabot alerts
- Secret scanning alerts (if enabled)

### Dependabot

**Status:** Enabled ✅

**Configuration:** `.github/dependabot.yml`

**What It Does:**

- Monitors Python dependencies (`poetry.lock`)
- Monitors npm dependencies (`autoarr/ui/package-lock.json`)
- Creates automated PRs for security updates
- Prioritizes CRITICAL and HIGH severity issues

**Alert Types:**

- Dependency vulnerabilities (CVEs)
- Outdated dependencies with security fixes
- Transitive dependency issues

---

## Security Best Practices

### For Maintainers

1. **Never Ignore Security Failures**

   - If Trivy blocks a release, fix the vulnerability first
   - Don't use `continue-on-error: true` for CRITICAL/HIGH

2. **Review Dependabot PRs Quickly**

   - Security updates should be merged ASAP
   - Test automated PRs before merging

3. **Monitor GitHub Security Tab**

   - Check weekly for new alerts
   - Address HIGH severity issues within 7 days
   - Address CRITICAL severity issues within 24 hours

4. **Keep Base Images Updated**

   - Regularly update `python:3.11-slim` in Dockerfile
   - Alpine packages should be kept current

5. **Verify SBOM and Provenance**
   - Periodically audit SBOM contents
   - Ensure provenance is being generated

### For Users

1. **Verify Checksums**

   ```bash
   # Download SHA256SUMS.txt from release
   sha256sum -c SHA256SUMS.txt
   ```

2. **Review Security Scan Reports**

   - Download `security-scan-X.Y.Z.txt` from releases
   - Check for any vulnerabilities before deploying

3. **Use Specific Version Tags**

   ```bash
   # Good: pinned version
   docker pull ghcr.io/feawservices/autoarr:0.8.0

   # Less secure: floating tag
   docker pull ghcr.io/feawservices/autoarr:latest
   ```

4. **Subscribe to Security Advisories**
   - Watch repository for security updates
   - Enable GitHub notifications for releases

---

## Responding to Vulnerabilities

### If a Vulnerability Is Found

1. **Assess Severity**

   - Check CVE details in NVD database
   - Determine exploitability in AutoArr context

2. **Create Private Security Advisory**

   - GitHub → Security → Advisories → New draft
   - Provide CVE details and affected versions

3. **Develop Fix**

   - Create patch in private fork if needed
   - Test thoroughly

4. **Release Security Update**

   - Create emergency patch release (e.g., 0.8.1)
   - Document in release notes
   - Notify users via GitHub Security Advisory

5. **Post-Mortem**
   - Document lessons learned
   - Improve scanning/testing if needed

### Vulnerability Disclosure Policy

**Security issues should be reported to:**

- GitHub Security Advisories (preferred)
- Or: security@your-domain.com

**Response Timeline:**

- **Acknowledgment:** Within 24 hours
- **Initial Assessment:** Within 72 hours
- **Fix Development:** 7-30 days (depending on severity)
- **Public Disclosure:** After fix is released

---

## Compliance & Standards

AutoArr's security scanning meets or exceeds:

- ✅ **OWASP Top 10** - Covered by CodeQL and Bandit
- ✅ **CWE/SANS Top 25** - Covered by CodeQL
- ✅ **NIST 800-53** - Container security controls
- ✅ **SLSA Level 3** - Build provenance and integrity
- ✅ **SBOM Requirements** - SPDX format SBOMs
- ✅ **Docker Bench** - Container security best practices

---

## Scanning Commands Reference

### Local Security Scans

```bash
# Python security scan
poetry run bandit -r autoarr/ -ll

# Dependency vulnerabilities
poetry run safety check

# Container scan (after building image)
docker build -t autoarr:local -f docker/Dockerfile.production .
trivy image autoarr:local --severity HIGH,CRITICAL

# Generate SBOM locally
docker buildx build --sbom=true -t autoarr:local -f docker/Dockerfile.production .
docker buildx imagetools inspect autoarr:local --format '{{json .SBOM}}'

# Check specific CVE
trivy image autoarr:local --vuln-type os,library --list-all-pkgs
```

### CI/Release Scans

```bash
# Trigger security scan workflow
gh workflow run ci.yml --ref main

# View security scan results
gh api repos/OWNER/REPO/code-scanning/alerts

# Download security report from release
gh release download v0.8.0 -p 'security-scan-*.txt'
```

---

## Additional Resources

- **Trivy Documentation**: https://aquasecurity.github.io/trivy/
- **SLSA Framework**: https://slsa.dev/
- **SBOM Guide**: https://www.cisa.gov/sbom
- **CodeQL Queries**: https://codeql.github.com/
- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **GitHub Security**: https://docs.github.com/en/code-security

---

## Summary

AutoArr's security scanning provides:

✅ **Multi-layered defense** - SAST, dependency scanning, container scanning
✅ **Continuous monitoring** - Every commit, PR, and release
✅ **Blocking on HIGH/CRITICAL** - Releases won't ship with serious vulnerabilities
✅ **Full transparency** - Security reports attached to releases
✅ **Supply chain security** - SBOM and SLSA provenance
✅ **Industry compliance** - Meets OWASP, NIST, SLSA standards

**Your users can trust AutoArr is secure by design.** 🔒

---

_Last Updated: 2025-12-08_
_Version: 1.0_
