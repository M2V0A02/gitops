# Getting Started - Quick Reference

## 🚀 30-Second Start

```bash
# 1. Update your GitHub username in ArgoCD manifests
sed -i 's/YOUR_USERNAME/your-github-username/g' argocd/*.yaml

# 2. Start VM (takes 10-15 minutes)
make vm-up

# 3. Get credentials
make argocd-pass

# 4. Access ArgoCD
open https://localhost:30000
```

---

## 📋 What Was Generated

### ✅ Production-Ready Flask Application
- **Location**: `app/`
- **Features**: REST API, Health checks, Prometheus metrics
- **Tests**: 17 unit tests with 70%+ coverage
- **Endpoints**:
  - `/health`, `/ready`, `/metrics`
  - `/api/items` (GET, POST)
  - `/api/items/<id>` (GET, PUT, DELETE)

### ✅ Multi-Stage Dockerfile
- **Location**: `app/Dockerfile`
- **Features**:
  - Optimized size (~150MB)
  - Non-root user
  - Health checks
  - Gunicorn production server

### ✅ Kubernetes Manifests
- **Base**: `k8s/base/` - Deployment, Service, ConfigMap
- **Overlays**: `k8s/overlays/{dev,staging,prod}`
- **Features**:
  - Kustomize for environment-specific configs
  - Health/readiness probes
  - Resource limits
  - Security contexts

### ✅ GitHub Actions CI/CD
- **CI Pipeline**: `.github/workflows/ci.yaml`
  - 6 jobs: lint, security, test, build, push, update-manifests
  - Matrix testing (Python 3.10, 3.11, 3.12)
  - Docker vulnerability scanning
  - Automatic manifest updates

- **CD Pipelines**:
  - `.github/workflows/cd-staging.yaml`
  - `.github/workflows/cd-prod.yaml`
  - Manual deployments with approval

### ✅ Infrastructure as Code
- **Vagrant**: `terraform/Vagrantfile`
  - Ubuntu 22.04 VM (4GB RAM, 2 CPU)
  - Port forwarding configured

- **Ansible**: `ansible/playbooks/`
  - Install Docker
  - Install K3s Kubernetes
  - Install ArgoCD
  - Setup namespaces

### ✅ ArgoCD Applications
- **Location**: `argocd/`
- **Apps**: dev (auto-sync), staging (manual), prod (manual)
- **Features**: Self-healing, auto-prune, retry logic

### ✅ Documentation
- `README.md` - Project overview
- `TECH_STACK.md` - Architecture and tech choices
- `PROJECT_GOALS.md` - Goals and success metrics
- `docs/SETUP_GUIDE.md` - Detailed setup instructions
- `docs/CI_CD_GUIDE.md` - CI/CD pipeline deep dive
- `gitops-cicd-testing-plan.md` - Original testing plan
- `Makefile` - Helper commands

---

## 🎯 Your Focus Areas

### 1. GitHub Actions CI Pipeline

**File**: `.github/workflows/ci.yaml`

**Test scenarios**:
```bash
# Test 1: Create PR (CI runs but doesn't deploy)
git checkout -b feature/test
# make changes
git push origin feature/test

# Test 2: Merge to develop (auto-deploy to dev)
git checkout develop
git merge feature/test
git push

# Test 3: Production release
git checkout main
git merge develop
git push
```

**Key features to explore**:
- [ ] Lint and security scanning
- [ ] Matrix testing across Python versions
- [ ] Docker build with caching
- [ ] Trivy vulnerability scanning
- [ ] Automatic image tagging strategy
- [ ] Manifest updates via yq
- [ ] GitHub Container Registry publishing

### 2. ArgoCD GitOps

**Access**: https://localhost:30000

**Test scenarios** (from PROJECT_GOALS.md):
- [ ] **Test 1**: Deploy new version (code → CI → ArgoCD → pods)
- [ ] **Test 2**: Rollback to previous version
- [ ] **Test 3**: Change ConfigMap values
- [ ] **Test 4**: Multi-environment deployment
- [ ] **Test 5**: Drift detection (manual kubectl edit)
- [ ] **Test 6**: Failed deployment handling

**Key features to explore**:
- [ ] Auto-sync vs manual sync
- [ ] Application health status
- [ ] Sync waves and hooks
- [ ] Diff view between Git and cluster
- [ ] History and rollback
- [ ] Resource visualization

---

## 📊 Success Metrics Checklist

From `PROJECT_GOALS.md`:

### CI Pipeline ✅
- [ ] Runs on every push/PR
- [ ] Lint passes (flake8, pylint, black)
- [ ] Security scan passes (bandit, safety, gitleaks)
- [ ] Tests pass with >70% coverage
- [ ] Docker builds successfully
- [ ] Trivy scan shows no critical issues
- [ ] Image pushed with correct tags
- [ ] Manifests updated automatically
- [ ] Total time < 5 minutes

### ArgoCD ✅
- [ ] Auto-sync works for dev
- [ ] Manual sync works for staging/prod
- [ ] Sync completes in < 3 minutes
- [ ] Health checks pass
- [ ] Rollback works
- [ ] Drift detection works
- [ ] Multi-environment deployments work

### End-to-End ✅
- [ ] Code change → production in < 15 minutes
- [ ] Zero-downtime deployments
- [ ] Full audit trail in Git

---

## 🛠️ Quick Commands

### VM Management
```bash
make vm-up          # Start VM
make vm-ssh         # SSH into VM
make vm-down        # Stop VM
make vm-destroy     # Delete VM
```

### Development
```bash
make test-app       # Run tests
make lint           # Run linters
make build-local    # Build Docker image
make run-local      # Run app locally
```

### Kubernetes
```bash
make get-kubeconfig # Get kubeconfig from VM
make argocd-pass    # Get ArgoCD password
make deploy-argocd  # Deploy ArgoCD apps
```

---

## 📝 Before You Start

### 1. Prerequisites Installed?
- [ ] Vagrant 2.3+
- [ ] VirtualBox 7.0+
- [ ] Ansible 2.15+
- [ ] Git 2.40+

### 2. GitHub Repository Setup
```bash
# Initialize and push to GitHub
git init
git add .
git commit -m "Initial commit: GitOps CI/CD project"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/gitops.git
git push -u origin main

# Create develop branch
git checkout -b develop
git push -u origin develop
```

### 3. Update Configuration
```bash
# Replace YOUR_USERNAME with your GitHub username
sed -i 's/YOUR_USERNAME/YOUR_ACTUAL_USERNAME/g' argocd/*.yaml
git add argocd/
git commit -m "Update ArgoCD manifests with GitHub username"
git push
```

### 4. Configure GitHub (optional)
- Settings → Environments → Create `staging` and `production`
- Add required reviewers for production
- Enable branch protection for `main`

---

## 🎓 Learning Path

### Week 1: CI Pipeline Mastery
1. Read `docs/CI_CD_GUIDE.md`
2. Create feature branch and PR
3. Watch CI pipeline run
4. Fix any failures
5. Experiment with different scenarios
6. Try breaking tests intentionally
7. Add security vulnerability (dependency) and see it caught

### Week 2: GitOps with ArgoCD
1. Start VM and access ArgoCD
2. Deploy dev application
3. Make code changes and watch auto-sync
4. Practice manual sync for staging
5. Try rollback scenario
6. Test drift detection
7. Explore ArgoCD UI features

### Week 3: Advanced Scenarios
1. Multi-environment promotion
2. Failed deployment handling
3. ConfigMap changes
4. Resource scaling
5. Custom sync waves
6. Notifications setup

---

## 🐛 Common Issues

### VM won't start
```bash
# Check VirtualBox
vboxmanage list vms

# Re-create
make vm-destroy
make vm-up
```

### CI fails on first run
- Check GitHub username updated in ArgoCD manifests
- Verify GitHub Actions has package write permission

### Can't access ArgoCD
```bash
# Check VM is running
make vm-ssh

# Check ArgoCD pods
kubectl get pods -n argocd
```

### Image pull fails in K8s
- For public GitHub repos: images are public by default
- For private repos: need to add imagePullSecret

---

## 📚 Documentation Structure

```
.
├── README.md                      # Project overview
├── GETTING_STARTED.md            # This file - quick start
├── PROJECT_GOALS.md              # Goals and metrics
├── TECH_STACK.md                 # Architecture details
├── gitops-cicd-testing-plan.md   # Testing roadmap
└── docs/
    ├── SETUP_GUIDE.md            # Detailed setup
    └── CI_CD_GUIDE.md            # CI/CD deep dive
```

**Read in this order**:
1. This file (GETTING_STARTED.md)
2. PROJECT_GOALS.md - understand what you're testing
3. docs/SETUP_GUIDE.md - detailed setup steps
4. docs/CI_CD_GUIDE.md - understand the pipelines
5. TECH_STACK.md - architecture deep dive

---

## 🎯 Next Actions

1. **Now**:
   ```bash
   make vm-up
   ```

2. **While VM starts** (10-15 min):
   - Read PROJECT_GOALS.md
   - Update GitHub username in argocd/*.yaml
   - Push code to GitHub

3. **When VM ready**:
   ```bash
   make argocd-pass
   open https://localhost:30000
   make deploy-argocd
   ```

4. **Start testing**:
   - Create feature branch
   - Make small code change
   - Push and watch CI/CD magic happen!

---

## 💡 Pro Tips

1. **Use the Makefile**: All common commands are there
2. **Watch logs**: `kubectl logs -f <pod> -n dev`
3. **ArgoCD CLI**: Install for easier debugging
4. **Git history**: `git log --oneline --graph --all`
5. **Test incrementally**: Don't try everything at once
6. **Document learnings**: Add notes to PROJECT_GOALS.md

---

## ✅ Day 1 Goals

- [ ] VM running successfully
- [ ] ArgoCD accessible
- [ ] Code pushed to GitHub
- [ ] First CI run completed
- [ ] Dev application deployed via ArgoCD
- [ ] Health check passing: `curl http://localhost:30080/health`

**Time estimate**: 1-2 hours including VM provisioning

---

Good luck! 🚀

For questions or issues, check:
- docs/SETUP_GUIDE.md - Troubleshooting section
- GitHub Actions logs for CI issues
- ArgoCD UI for deployment issues
