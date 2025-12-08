# Security Policy

## Overview

AutoArr takes security seriously. This document outlines our security practices, supply chain security, and how to report vulnerabilities.

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.8.x   | :white_check_mark: |
| < 0.8   | :x:                |

## Container Security

AutoArr implements enterprise-grade container security practices.

### Supply Chain Security

All official container images include:

- **SBOM (Software Bill of Materials)**: CycloneDX format attached to images
- **Cosign Signatures**: Keyless Sigstore signing for image verification
- **SLSA Provenance**: Build provenance attestations (Level 2)
- **Trivy Scanning**: Blocking scans for HIGH/CRITICAL vulnerabilities

### Verifying Container Images

```bash
# Verify image signature (requires cosign installed)
cosign verify ghcr.io/feawservices/autoarr:latest \
  --certificate-identity-regexp="https://github.com/FEAWServices/autoarr" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com"

# Download and view SBOM
cosign download sbom ghcr.io/feawservices/autoarr:latest > sbom.json

# Verify SLSA provenance
cosign verify-attestation ghcr.io/feawservices/autoarr:latest \
  --type slsaprovenance \
  --certificate-identity-regexp="https://github.com/FEAWServices/autoarr" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com"
```

### Official Image Registries

| Registry                  | Image                                   |
| ------------------------- | --------------------------------------- |
| GitHub Container Registry | `ghcr.io/feawservices/autoarr:latest`   |
| Docker Hub                | `docker.io/feawservices/autoarr:latest` |

## Security Features

### Authentication & Authorization

- [x] **CORS Configuration**: Properly configured for local development
- [x] **Rate Limiting**: Implemented with configurable limits per endpoint
- [ ] **API Key Authentication**: Planned for v1.0
- [ ] **JWT Token Support**: Planned for v1.1

### Data Protection

- [x] **Environment Variables**: All secrets loaded from environment
- [x] **Secure Configuration**: No hardcoded credentials in code
- [x] **API Key Masking**: Sensitive keys masked in UI and logs
- [ ] **Encryption at Rest**: Database encryption (planned)
- [ ] **Encryption in Transit**: HTTPS enforced in production (deployment-dependent)

### Input Validation

- [x] **Pydantic Validation**: All API inputs validated
- [x] **SQL Injection Protection**: Parameterized queries via SQLAlchemy ORM
- [x] **XSS Protection**: Input sanitization
- [x] **CSRF Protection**: Token-based API (stateless)

### Secure Headers

- [x] **X-Content-Type-Options**: Set to `nosniff`
- [x] **Security Middleware**: Custom security headers middleware
- [ ] **Content-Security-Policy**: To be configured
- [ ] **Strict-Transport-Security**: To be configured for production

### Dependencies

- [x] **Dependency Management**: Poetry for lockfile-based dependencies
- [x] **Automated Security Scans**: Dependabot configured
- [x] **Vulnerability Scanning**: Trivy scans in CI/CD
- [x] **Static Analysis**: Bandit for Python security linting

## Security Checklist

### Development

- [x] No hardcoded secrets (use environment variables)
- [x] All database queries parameterized
- [x] Input validation on all endpoints
- [x] Rate limiting implemented
- [x] CORS configured properly
- [x] Secrets stored securely in environment
- [x] Dependencies managed via Poetry
- [x] Pre-commit hooks for security checks
- [ ] HTTPS enforced in production (deployment-dependent)
- [ ] CSP headers configured

### Production Deployment

- [ ] Change default `SECRET_KEY` to strong random value
- [ ] Use HTTPS/TLS for all connections
- [ ] Set `app_env=production` in environment
- [ ] Restrict CORS origins to production domains
- [ ] Configure firewall rules
- [ ] Use secure database credentials
- [ ] Enable database connection encryption
- [ ] Implement proper logging without sensitive data
- [ ] Regular security updates and patches

### API Keys & Secrets

- [x] `SECRET_KEY`: Must be changed in production
- [x] `SABNZBD_API_KEY`: Load from environment
- [x] `SONARR_API_KEY`: Load from environment
- [x] `RADARR_API_KEY`: Load from environment
- [x] `PLEX_TOKEN`: Load from environment
- [x] `CLAUDE_API_KEY`: Load from environment
- [x] `DATABASE_URL`: Load from environment (if used)
- [x] `REDIS_URL`: Load from environment (if used)

### Example Secure Configuration

```bash
# .env file (DO NOT commit this file!)
SECRET_KEY=your-super-secret-random-key-at-least-32-characters-long
SABNZBD_API_KEY=your-sabnzbd-api-key
SONARR_API_KEY=your-sonarr-api-key
RADARR_API_KEY=your-radarr-api-key
PLEX_TOKEN=your-plex-token
CLAUDE_API_KEY=your-claude-api-key
DATABASE_URL=sqlite:///./autoarr.db
APP_ENV=production
CORS_ORIGINS=https://your-domain.com
```

## Known Security Issues

### Critical

None currently identified.

### High

None currently identified.

### Medium

- **Authentication**: No authentication system implemented yet. Intended for trusted home network deployment behind reverse proxy.

### Low

None currently identified.

## Security Best Practices

### For Developers

1. **Never commit secrets**: Use `.gitignore` to exclude `.env` files
2. **Use environment variables**: All configuration should come from environment
3. **Validate all inputs**: Use Pydantic models for request validation
4. **Sanitize outputs**: Escape HTML/JS in responses
5. **Use parameterized queries**: Never construct SQL with string concatenation
6. **Keep dependencies updated**: Run `poetry update` regularly
7. **Review PRs for security**: Check for hardcoded secrets, SQL injection, etc.

### For Deployers

1. **Use strong secrets**: Generate random keys with `openssl rand -hex 32`
2. **Enable HTTPS**: Use reverse proxy (nginx, Traefik) with TLS
3. **Restrict network access**: Use firewall rules to limit exposure
4. **Monitor logs**: Set up log aggregation and alerting
5. **Regular backups**: Backup database and configuration regularly
6. **Update regularly**: Apply security patches promptly
7. **Verify container images**: Use cosign to verify image signatures

## Reporting a Vulnerability

### How to Report

If you discover a security vulnerability, please:

1. **DO NOT** create a public GitHub issue
2. Email security concerns to: **security@autoarr.io**
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity
  - Critical: Within 24-48 hours
  - High: Within 7 days
  - Medium: Within 30 days
  - Low: Next release cycle

### Disclosure Policy

We follow responsible disclosure:

1. Issue is reported privately
2. We confirm and investigate
3. Fix is developed and tested
4. Fix is released
5. Public disclosure after 90 days or after fix is released

### Credit

We appreciate security researchers who help improve AutoArr. With your permission, we will credit you in our release notes and security advisories.

## Security Testing

### Automated Tests

We maintain comprehensive security tests:

- **Static Analysis**: Bandit for Python code scanning
- **Dependency Scanning**: Dependabot + Trivy for known vulnerabilities
- **Container Scanning**: Trivy HIGH/CRITICAL blocking in CI
- **Unit Tests**: Security-focused test suite (`tests/security/`)
- **Integration Tests**: API security tests

### CI/CD Security

Every build includes:

- Bandit static analysis
- Safety dependency checks
- Trivy container vulnerability scanning
- SBOM generation
- Image signing

## Security Resources

### Tools Used

- **Bandit**: Python security linter
- **Safety**: Dependency vulnerability scanner
- **Trivy**: Container vulnerability scanner
- **Cosign**: Container image signing
- **Syft**: SBOM generation
- **Dependabot**: Automated dependency updates

### References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Docker Security](https://docs.docker.com/engine/security/)
- [Sigstore](https://sigstore.dev/)
- [SLSA](https://slsa.dev/)

## Compliance

### Standards

- **OWASP Top 10**: Mitigation strategies implemented
- **CWE Top 25**: Common weakness coverage
- **Supply Chain Security**: SBOM + provenance attestations

### Privacy

- **No PII Collection**: AutoArr does not collect personal information
- **Local Deployment**: All data stays in your infrastructure
- **No Telemetry**: No usage data sent to external services
- **Open Source**: Full code transparency (GPL-3.0)

## Contact

For security-related questions or concerns:

- **Email**: security@autoarr.io
- **GitHub Security Advisories**: [Security Advisories](https://github.com/FEAWServices/autoarr/security/advisories)

---

Last updated: 2025-12-08
