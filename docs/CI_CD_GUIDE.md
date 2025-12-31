# CI/CD Pipeline Guide

## GitHub Actions CI Pipeline Overview

The CI pipeline is production-ready with multiple stages for quality, security, and deployment.

### Pipeline Stages

```
┌─────────────────────────────────────────────────────────────┐
│                    TRIGGER: Push/PR                          │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
        ┌───────▼──────┐       ┌───────▼──────┐
        │   Lint       │       │   Security   │
        │              │       │              │
        │ • flake8     │       │ • bandit     │
        │ • pylint     │       │ • safety     │
        │ • black      │       │ • gitleaks   │
        └───────┬──────┘       └───────┬──────┘
                │                       │
                └───────────┬───────────┘
                            │
                    ┌───────▼──────┐
                    │    Test      │
                    │              │
                    │ • pytest     │
                    │ • coverage   │
                    │ • matrix     │
                    └───────┬──────┘
                            │
                    ┌───────▼──────┐
                    │    Build     │
                    │              │
                    │ • Docker     │
                    │ • Trivy scan │
                    └───────┬──────┘
                            │
            ┌───────────────┴───────────────┐
            │   If main/develop branch      │
            └───────────────┬───────────────┘
                            │
                ┌───────────┴────────────┐
                │                        │
        ┌───────▼──────┐      ┌─────────▼─────────┐
        │     Push     │      │ Update Manifests  │
        │              │      │                   │
        │ • GHCR       │      │ • yq edit         │
        │ • Tag image  │      │ • Git commit      │
        └──────────────┘      └───────────────────┘
```

---

## CI Pipeline Configuration

### File: `.github/workflows/ci.yaml`

#### Job 1: Code Quality & Linting

**Purpose**: Ensure code meets quality standards

**Tools**:
- `flake8`: PEP8 style checking
- `pylint`: Static analysis (score ≥ 8.0)
- `black`: Code formatting check

**Success Criteria**:
- No flake8 violations
- Pylint score ≥ 8.0
- Code is properly formatted

**When it runs**: Every push, every PR

---

#### Job 2: Security Scanning

**Purpose**: Identify security vulnerabilities

**Tools**:
- `bandit`: Python security scanner
- `safety`: Dependency vulnerability check
- `gitleaks`: Secrets detection

**Success Criteria**:
- No HIGH/CRITICAL security issues
- No exposed secrets
- All dependencies safe

**When it runs**: Every push, every PR

---

#### Job 3: Unit Tests

**Purpose**: Verify code functionality

**Features**:
- Matrix testing (Python 3.10, 3.11, 3.12)
- Code coverage reporting
- Coverage threshold: 70%
- Codecov integration

**Success Criteria**:
- All tests pass
- Coverage ≥ 70%
- No test failures across all Python versions

**When it runs**: Every push, every PR

---

#### Job 4: Build Docker Image

**Purpose**: Build and validate container

**Features**:
- Multi-stage Dockerfile
- Docker BuildKit caching
- Container testing (health check)
- Trivy vulnerability scanning
- SARIF upload to GitHub Security

**Success Criteria**:
- Image builds successfully
- Health check passes
- No CRITICAL/HIGH vulnerabilities

**When it runs**: Every push, every PR (after tests pass)

---

#### Job 5: Push Docker Image

**Purpose**: Publish container to registry

**Features**:
- GitHub Container Registry (GHCR)
- Multiple tagging strategies:
  - `develop-{sha}` for develop branch
  - `main-{sha}` for main branch
  - `latest` for main branch only
- Build provenance attestation

**Success Criteria**:
- Image successfully pushed
- Tags correctly applied

**When it runs**: Only on push to main/develop (not PRs)

---

#### Job 6: Update Kubernetes Manifests

**Purpose**: Update image tags in K8s manifests for GitOps

**Process**:
1. Install `yq` tool
2. Update kustomization.yaml with new image tag
3. Commit changes to Git
4. Push to trigger ArgoCD sync

**Success Criteria**:
- Kustomization.yaml updated
- Changes committed and pushed

**When it runs**: Only on push to main/develop (after image push)

---

## CD Pipeline Configuration

### Workflow 1: CD to Staging

**File**: `.github/workflows/cd-staging.yaml`

**Trigger**: Manual (workflow_dispatch)

**Input**: Image tag to deploy

**Process**:
1. Checkout code
2. Update staging overlay
3. Commit and push
4. ArgoCD syncs automatically

**Environment Protection**:
- Requires manual approval (optional)
- Environment: `staging`

---

### Workflow 2: CD to Production

**File**: `.github/workflows/cd-prod.yaml`

**Trigger**: Manual (workflow_dispatch)

**Input**: Image tag to deploy

**Process**:
1. Checkout code
2. Update production overlay
3. Commit and push
4. ArgoCD syncs (manual in UI)

**Environment Protection**:
- Requires manual approval
- Environment: `production`
- Recommended: 2 reviewers required

---

## Branch Strategy

### Branch: `develop`

**Purpose**: Development/integration branch

**CI Behavior**:
- Full CI runs (lint, security, test, build)
- Docker image built and pushed
- Tagged as: `develop-{sha}`
- Dev manifests auto-updated
- **Auto-deploys to dev environment**

### Branch: `main`

**Purpose**: Production-ready code

**CI Behavior**:
- Full CI runs
- Docker image built and pushed
- Tagged as: `main-{sha}` and `latest`
- Staging manifests updated
- **Manual deployment to staging/prod**

### Feature Branches

**Pattern**: `feature/*`

**CI Behavior**:
- Full CI runs (lint, security, test, build)
- Docker image built but NOT pushed
- No deployment
- Blocks PR if CI fails

---

## Testing the CI Pipeline

### Test 1: PR from Feature Branch

```bash
# Create feature branch
git checkout -b feature/test-ci
echo "print('test')" >> app/app.py

# Push and create PR
git add .
git commit -m "Test CI pipeline"
git push origin feature/test-ci
```

**Expected**:
- ✅ Lint job runs
- ✅ Security job runs
- ✅ Test job runs (3 Python versions)
- ✅ Build job runs
- ❌ Push job SKIPPED (not main/develop)
- ❌ Manifest update SKIPPED

**Check**:
- GitHub Actions tab shows all checks
- PR shows status checks

---

### Test 2: Merge to Develop

```bash
# Merge PR to develop
git checkout develop
git merge feature/test-ci
git push origin develop
```

**Expected**:
- ✅ All CI jobs run
- ✅ Docker image pushed: `ghcr.io/user/gitops:develop-abc123`
- ✅ Dev kustomization.yaml updated
- ✅ ArgoCD auto-syncs to dev namespace
- ⏱️ Total time: ~5 minutes

**Verify**:
```bash
# Check image in registry
# GitHub → Packages

# Check git commit
git log --oneline -n 2

# Check ArgoCD
# UI → gitops-demo-dev → Synced

# Check pods
kubectl get pods -n dev
```

---

### Test 3: Promote to Staging

```bash
# Merge develop to main
git checkout main
git pull
git merge develop
git push origin main
```

**Expected**:
- ✅ CI runs on main
- ✅ Image pushed: `ghcr.io/user/gitops:main-abc123` and `:latest`
- ✅ Staging kustomization.yaml updated
- ⏸️ ArgoCD shows "Out of Sync" (manual sync required)

**Manual Step**:
1. Open ArgoCD UI
2. Select `gitops-demo-staging`
3. Click "SYNC" button
4. Wait for deployment

---

### Test 4: Rollback Scenario

```bash
# Deploy "broken" code to develop
git checkout develop
echo "import nonexistent" >> app/app.py
git add .
git commit -m "Intentional break"
git push origin develop
```

**Expected**:
- ❌ Test job fails
- ❌ Build blocked
- ❌ No deployment

**Recovery**:
```bash
git revert HEAD
git push origin develop
```

---

## CI/CD Metrics

### Performance Targets

| Metric | Target | Actual |
|--------|--------|--------|
| Lint time | < 1 min | ~30s |
| Security scan | < 2 min | ~1m |
| Tests (single version) | < 2 min | ~1m |
| Docker build | < 3 min | ~2m |
| Total CI time | < 5 min | ~4m |
| ArgoCD sync time | < 3 min | ~1-2m |
| **Full deployment** | **< 8 min** | **~6m** |

### Success Rates

| Stage | Target | Description |
|-------|--------|-------------|
| CI success rate | > 95% | For valid code |
| Security scan pass | 100% | No critical issues |
| Test coverage | > 70% | Code coverage |
| Deployment success | > 99% | GitOps sync |

---

## Advanced CI Features

### Caching

**Docker Layer Caching**:
```yaml
cache-from: type=gha
cache-to: type=gha,mode=max
```
- Speeds up builds by ~50%
- Shares cache across workflows

**Pip Caching**:
```yaml
- uses: actions/setup-python@v5
  with:
    cache: 'pip'
```
- Faster dependency installation

---

### Matrix Testing

```yaml
strategy:
  matrix:
    python-version: ['3.10', '3.11', '3.12']
```

**Benefits**:
- Ensures compatibility across versions
- Runs in parallel
- Catches version-specific issues

---

### Security Scanning Layers

1. **Code**: bandit (SAST)
2. **Dependencies**: safety
3. **Secrets**: gitleaks
4. **Container**: Trivy
5. **SARIF upload**: GitHub Security tab

---

### Build Attestation

```yaml
- uses: actions/attest-build-provenance@v1
```

**Benefits**:
- Cryptographic proof of build
- Supply chain security
- Verifiable provenance

---

## Troubleshooting CI

### Tests Failing

```bash
# Run locally first
cd app
pip install -r requirements-dev.txt
pytest -v
```

### Docker Build Failing

```bash
# Build locally
cd app
docker build -t test .
```

### Image Push Failing

**Check**:
- GITHUB_TOKEN has package write permission
- Repository settings → Actions → Workflow permissions

### Manifest Update Failing

**Check**:
- yq syntax correct
- Git user configured
- Branch not protected (or allow Actions to bypass)

---

## CI/CD Best Practices Applied

✅ **Fast Feedback**: Parallel jobs, < 5 min total
✅ **Fail Fast**: Lint and security run first
✅ **Test Pyramid**: Unit tests with coverage
✅ **Security**: Multi-layer scanning
✅ **Reproducible**: Matrix builds, caching
✅ **Declarative**: GitOps for deployments
✅ **Auditable**: All changes in Git
✅ **Safe**: Manual approvals for prod

---

## Next Steps

1. Set up branch protection rules
2. Configure required reviewers for prod
3. Add Slack/email notifications
4. Implement integration tests
5. Add performance tests
6. Set up monitoring alerts
