# Setup Guide - GitOps CI/CD Project

## Prerequisites

### Software Requirements
Install the following on your local machine:

```bash
# Check versions
vagrant --version    # 2.3+
vboxmanage --version # 7.0+
ansible --version    # 2.15+
git --version        # 2.40+
```

### Installation Links
- **Vagrant**: https://developer.hashicorp.com/vagrant/downloads
- **VirtualBox**: https://www.virtualbox.org/wiki/Downloads
- **Ansible**: `pip install ansible` or use package manager

---

## Quick Start (5 minutes)

### 1. Clone and Setup Repository

```bash
# Clone your repository
git clone https://github.com/YOUR_USERNAME/gitops.git
cd gitops

# Update ArgoCD application manifests with your repo URL
sed -i 's|YOUR_USERNAME|your-github-username|g' argocd/*.yaml
```

### 2. Start the VM

```bash
cd terraform
vagrant up
```

This will:
- Create Ubuntu 22.04 VM (4GB RAM, 2 CPU)
- Install Docker
- Install K3s Kubernetes
- Install ArgoCD
- Create dev/staging/prod namespaces

**Wait time**: ~10-15 minutes

### 3. Get Access Credentials

```bash
# SSH into the VM
vagrant ssh

# Get ArgoCD password
cat ~/argocd-credentials.txt

# Get kubeconfig
sudo cat /etc/rancher/k3s/k3s.yaml
```

### 4. Access ArgoCD UI

- **URL**: https://localhost:30000
- **Username**: admin
- **Password**: From argocd-credentials.txt

Accept the self-signed certificate warning.

---

## Detailed Setup Steps

### Step 1: Configure Git Repository

1. **Push code to GitHub**:
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/gitops.git
git push -u origin main
```

2. **Create develop branch**:
```bash
git checkout -b develop
git push -u origin develop
```

3. **Update ArgoCD manifests**:
Edit `argocd/*.yaml` and replace `YOUR_USERNAME` with your GitHub username.

### Step 2: Configure GitHub Actions

1. **Enable GitHub Container Registry**:
   - Go to Settings → Packages
   - Enable "Improved container support"

2. **Configure GitHub Secrets** (if needed for private registries):
   - Go to Settings → Secrets and variables → Actions
   - Add: `DOCKER_USERNAME`, `DOCKER_PASSWORD` (if using Docker Hub)

3. **Set up GitHub Environments**:
   - Go to Settings → Environments
   - Create: `staging`, `production`
   - Add protection rules (required reviewers)

### Step 3: Configure Local kubectl

```bash
# From your host machine, get kubeconfig
cd gitops/terraform
vagrant ssh -c "sudo cat /etc/rancher/k3s/k3s.yaml" > kubeconfig

# Edit kubeconfig - change server IP
sed -i 's/127.0.0.1/192.168.56.10/g' kubeconfig

# Use the kubeconfig
export KUBECONFIG=$(pwd)/kubeconfig

# Test connection
kubectl get nodes
kubectl get pods -A
```

### Step 4: Deploy ArgoCD Applications

```bash
# Apply ArgoCD application manifests
kubectl apply -f ../argocd/dev-application.yaml
kubectl apply -f ../argocd/staging-application.yaml
kubectl apply -f ../argocd/prod-application.yaml

# Check ArgoCD applications
kubectl get applications -n argocd
```

### Step 5: Build and Push Initial Docker Image

```bash
# Build locally first (optional)
cd ../app
docker build -t ghcr.io/YOUR_USERNAME/gitops:latest .

# Or push code and let CI build it
git add .
git commit -m "Add application code"
git push origin develop
```

---

## Testing the CI/CD Pipeline

### Test 1: Automatic Dev Deployment

```bash
# Make a change to the app
cd app
echo "# Updated" >> README.md

# Commit and push to develop
git add .
git commit -m "Test CI/CD pipeline"
git push origin develop
```

**Watch**:
1. GitHub Actions → CI workflow runs
2. Docker image builds and pushes
3. Kustomization updated with new image tag
4. ArgoCD syncs automatically (dev environment)
5. Check pods: `kubectl get pods -n dev`

### Test 2: Manual Staging Deployment

```bash
# Merge develop to main
git checkout main
git merge develop
git push origin main
```

**Then**:
1. Go to ArgoCD UI
2. Find `gitops-demo-staging` application
3. Click "Sync" button
4. Check: `kubectl get pods -n staging`

### Test 3: Production Deployment

```bash
# Use GitHub Actions workflow dispatch
# Go to Actions → "CD - Deploy to Production"
# Click "Run workflow"
# Enter image tag from previous build
```

---

## Verifying Everything Works

### Check K3s Cluster
```bash
vagrant ssh
kubectl get nodes
kubectl get pods -A
kubectl get namespaces
```

### Check ArgoCD
```bash
# Via UI
https://localhost:30000

# Via CLI
kubectl get applications -n argocd
kubectl describe application gitops-demo-dev -n argocd
```

### Check Application
```bash
# Port-forward to access app
kubectl port-forward -n dev svc/dev-gitops-demo-app 8080:80

# Test in another terminal
curl http://localhost:8080/health
curl http://localhost:8080/api/items
```

---

## Troubleshooting

### VM won't start
```bash
# Check VirtualBox is running
vboxmanage list vms

# Destroy and recreate
vagrant destroy -f
vagrant up
```

### Ansible provisioning fails
```bash
# Re-run provisioning
vagrant provision

# Or SSH and run manually
vagrant ssh
```

### ArgoCD can't access Git repo
```bash
# If private repo, add SSH key to ArgoCD
kubectl -n argocd create secret generic github-ssh \
  --from-file=sshPrivateKey=$HOME/.ssh/id_rsa
```

### CI workflow fails
- Check GitHub Actions logs
- Verify Docker registry permissions
- Check secrets are configured

### Pods won't start
```bash
# Check pod status
kubectl get pods -n dev
kubectl describe pod <pod-name> -n dev
kubectl logs <pod-name> -n dev

# Check image pull
kubectl get events -n dev
```

---

## Daily Workflow

### Development Cycle
```bash
# 1. Create feature branch
git checkout -b feature/new-feature

# 2. Make changes
vim app/app.py

# 3. Test locally (optional)
cd app
python -m pytest
docker build -t test .

# 4. Push and create PR
git add .
git commit -m "Add new feature"
git push origin feature/new-feature

# 5. Create PR in GitHub
# 6. Wait for CI to pass
# 7. Merge to develop → auto-deploys to dev
```

### Promote to Staging
```bash
# Merge develop to main
git checkout main
git pull
git merge develop
git push

# Manually sync in ArgoCD UI
```

### Promote to Production
```bash
# Use GitHub Actions workflow
# or manually sync in ArgoCD with approval
```

---

## Cleanup

### Stop VM (preserve state)
```bash
cd terraform
vagrant halt
```

### Delete everything
```bash
cd terraform
vagrant destroy -f
```

### Clean Docker images
```bash
docker system prune -a
```

---

## Next Steps

1. ✅ Complete all tests from PROJECT_GOALS.md
2. ✅ Try rollback scenario in ArgoCD
3. ✅ Test drift detection
4. ✅ Add your own features to the app
5. ✅ Experiment with different CI/CD scenarios

---

## Useful Commands Reference

### Vagrant
```bash
vagrant status              # Check VM status
vagrant ssh                 # SSH into VM
vagrant halt                # Stop VM
vagrant up                  # Start VM
vagrant destroy             # Delete VM
vagrant provision           # Re-run Ansible
```

### kubectl
```bash
kubectl get pods -A                           # All pods
kubectl get applications -n argocd            # ArgoCD apps
kubectl logs <pod> -n <namespace>            # Pod logs
kubectl describe pod <pod> -n <namespace>    # Pod details
kubectl port-forward -n dev svc/app 8080:80  # Access service
```

### ArgoCD CLI (optional)
```bash
# Install
curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x /usr/local/bin/argocd

# Login
argocd login localhost:30000 --username admin --password <password> --insecure

# List apps
argocd app list

# Sync app
argocd app sync gitops-demo-dev

# Rollback
argocd app rollback gitops-demo-dev
```

---

## Resources

- [K3s Documentation](https://docs.k3s.io/)
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Kustomize Documentation](https://kustomize.io/)
