.PHONY: help vm-up vm-down vm-ssh vm-destroy test-app lint build-local

help:
	@echo "GitOps CI/CD Project - Makefile Commands"
	@echo ""
	@echo "VM Management:"
	@echo "  make vm-up         - Start the VM and provision infrastructure"
	@echo "  make vm-down       - Stop the VM"
	@echo "  make vm-ssh        - SSH into the VM"
	@echo "  make vm-destroy    - Destroy the VM completely"
	@echo "  make vm-provision  - Re-run Ansible provisioning"
	@echo ""
	@echo "Application:"
	@echo "  make test-app      - Run application tests"
	@echo "  make lint          - Run code linting"
	@echo "  make build-local   - Build Docker image locally"
	@echo "  make run-local     - Run app locally with Docker"
	@echo ""
	@echo "Kubernetes:"
	@echo "  make get-kubeconfig - Get kubeconfig from VM"
	@echo "  make argocd-pass    - Get ArgoCD admin password"
	@echo "  make deploy-argocd  - Deploy ArgoCD applications"
	@echo ""
	@echo "Development:"
	@echo "  make install-deps   - Install Python dependencies"
	@echo "  make clean          - Clean temporary files"

# VM Management
vm-up:
	cd terraform && vagrant up

vm-down:
	cd terraform && vagrant halt

vm-ssh:
	cd terraform && vagrant ssh

vm-destroy:
	cd terraform && vagrant destroy -f

vm-provision:
	cd terraform && vagrant provision

# Application
test-app:
	cd app && pip install -r requirements-dev.txt && pytest

lint:
	cd app && flake8 . && pylint app.py

build-local:
	cd app && docker build -t gitops-demo-app:local .

run-local:
	docker run -d --name gitops-demo -p 5000:5000 gitops-demo-app:local
	@echo "App running at http://localhost:5000"
	@echo "Health check: curl http://localhost:5000/health"

stop-local:
	docker stop gitops-demo && docker rm gitops-demo

# Kubernetes
get-kubeconfig:
	cd terraform && vagrant ssh -c "sudo cat /etc/rancher/k3s/k3s.yaml" > kubeconfig
	@sed -i 's/127.0.0.1/192.168.56.10/g' terraform/kubeconfig
	@echo "Kubeconfig saved to terraform/kubeconfig"
	@echo "Use: export KUBECONFIG=\$$(pwd)/terraform/kubeconfig"

argocd-pass:
	cd terraform && vagrant ssh -c "cat ~/argocd-credentials.txt"

deploy-argocd:
	kubectl apply -f argocd/dev-application.yaml
	kubectl apply -f argocd/staging-application.yaml
	kubectl apply -f argocd/prod-application.yaml
	@echo "ArgoCD applications deployed"

# Development
install-deps:
	cd app && pip install -r requirements-dev.txt

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete
	rm -f terraform/kubeconfig
