# SBOM & SCA Summary

## Metadata
- **Commit**: Automated scan via CI workflow
- **SBOM Tool**: anchore/syft:v1.5.0 (CycloneDX JSON format)
- **SCA Tool**: anchore/grype:v0.78.0
- **Generated**: 2025-11-28 (UTC)
- **Workflow**: `.github/workflows/ci-sbom-sca.yml`

## Severity Counts
- **High**: 1
- **Medium**: 1
- **Total vulnerabilities**: 2

## Critical/High Findings

### 1. [High] GHSA-f96h-pmfr-66vw / CVE-2024-47874
- **Package**: starlette@0.38.6
- **Description**: Denial of service (DoS) via multipart/form-data - Starlette treats multipart/form-data parts without a filename as text form fields and buffers those in byte strings with no size limit. This allows an attacker to upload arbitrary large form fields and cause memory exhaustion.
- **Fix Available**: Yes, upgrade to version 0.40.0+
- **CVSS Score**: 8.7 (High)
- **Fix State**: fixed
- **Advisory**: https://github.com/advisories/GHSA-f96h-pmfr-66vw

### 2. [Medium] GHSA-2c2j-9gv5-cj73 / CVE-2025-54121
- **Package**: starlette@0.38.6
- **Description**: Possible denial-of-service vector when parsing large files in multipart forms - blocks the main thread to roll the file over to disk, preventing new connections.
- **Fix Available**: Yes, upgrade to version 0.47.2+
- **CVSS Score**: 5.3 (Medium)
- **Fix State**: fixed
- **Advisory**: https://github.com/advisories/GHSA-2c2j-9gv5-cj73

## Action Plan

### Immediate Actions (High Severity)
1. **Upgrade starlette** from 0.38.6 to latest stable version (≥0.47.2) to fix both vulnerabilities
   - Update in `requirements.txt` or `pyproject.toml`
   - Test compatibility with FastAPI and application code
   - Verify multipart/form-data handling still works as expected

### Risk Assessment
- **Impact**: Both vulnerabilities affect DoS scenarios with multipart form handling
- **Exploitability**: Network accessible without authentication (CVSS AV:N/PR:N)
- **Current Risk**: Medium-High - application uses FastAPI (built on Starlette) and likely accepts form data
- **Mitigation Priority**: High - fix available, low migration effort

### Waivers
- If upgrade is delayed, consider temporary waiver with justification (see `task/templates/policy/waivers.yml`)
- Waiver should include:
  - Timeline for upgrade (max 30 days)
  - Risk acceptance from project owner
  - Compensating controls (e.g., rate limiting, request size limits)

## Dependencies Scanned
Based on SBOM, the following dependencies were analyzed:
- Python packages from project requirements
- Transitive dependencies from virtual environment (`.venv/`)

## Next Steps
1. Review this summary and plan remediation
2. Create Issue/PR for starlette upgrade
3. If upgrade not feasible immediately, document waiver in `task/templates/policy/waivers.yml`
4. Re-run SCA after fixes to verify resolution
5. Integrate findings into DS section of final project report

## Reproducibility
To reproduce this scan locally:
```bash
# Generate SBOM
docker run --rm -v $PWD:/work -w /work anchore/syft:v1.5.0 packages dir:. -o cyclonedx-json > EVIDENCE/P09/sbom.json

# Run SCA
docker run --rm -v $PWD:/work -w /work anchore/grype:v0.78.0 sbom:/work/EVIDENCE/P09/sbom.json -o json > EVIDENCE/P09/sca_report.json
```

## References
- SBOM: `EVIDENCE/P09/sbom.json`
- Full SCA Report: `EVIDENCE/P09/sca_report.json`
- Project Vulnerability Management Policy: `project/69_sbom-vuln-mgmt.md` (if exists)
- Waiver Template: `task/templates/policy/waivers.yml`
