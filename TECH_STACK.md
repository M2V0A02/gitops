# Технологический стек проекта

## Выбранные технологии

### Инфраструктура
- **Платформа**: Virtual Machines (Vagrant + VirtualBox)
- **Провижининг**: Terraform (для создания VM)
- **Конфигурация**: Ansible (для настройки VM)
- **ОС**: Ubuntu 22.04 LTS

### Приложение
- **Язык**: Python 3.11
- **Фреймворк**: Flask
- **Контейнеризация**: Docker

### CI/CD Pipeline
- **CI**: GitHub Actions
- **Регистр образов**: Docker Hub / GitHub Container Registry
- **CD**: ArgoCD (GitOps)

### Kubernetes
- **Дистрибутив**: K3s (легковесный Kubernetes для VM)
- **Установка**: Через Ansible
- **Управление манифестами**: Kustomize

### GitOps
- **Инструмент**: ArgoCD
- **Паттерн**: Separate repository для app code и k8s manifests (опционально)

---

## Архитектура решения

```
┌─────────────────────────────────────────────────────────────┐
│                     Developer Workflow                       │
└─────────────────────────────────────────────────────────────┘
                            │
                    git push (code)
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Repository                        │
│  ┌────────────────┐              ┌─────────────────┐        │
│  │  Application   │              │  K8s Manifests  │        │
│  │     Code       │              │  (k8s/...)      │        │
│  └────────────────┘              └─────────────────┘        │
└─────────────────────────────────────────────────────────────┘
         │                                    │
         │ trigger                            │ watch
         ▼                                    │
┌──────────────────────┐                     │
│   GitHub Actions     │                     │
│   ─────────────      │                     │
│   1. Build           │                     │
│   2. Test            │                     │
│   3. Build Docker    │                     │
│   4. Push to Registry│                     │
│   5. Update manifest │─────────────────────┘
└──────────────────────┘              (git commit new image tag)
                                              │
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Virtual Machine(s)                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    K3s Cluster                       │   │
│  │  ┌────────────────────────────────────────────────┐  │   │
│  │  │              ArgoCD                            │  │   │
│  │  │  - Monitors Git repo                          │  │   │
│  │  │  - Syncs K8s manifests                        │  │   │
│  │  │  - Deploys application                        │  │   │
│  │  └────────────────────────────────────────────────┘  │   │
│  │                                                       │   │
│  │  ┌────────────────────────────────────────────────┐  │   │
│  │  │         Application Pods                       │  │   │
│  │  │  - Flask app containers                        │  │   │
│  │  └────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Provisioned by: Terraform                                  │
│  Configured by: Ansible                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Структура проекта (обновленная)

```
.
├── app/                          # Flask приложение
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
│
├── terraform/                    # Terraform конфигурация для VM
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── Vagrantfile              # Локальная разработка
│
├── ansible/                      # Ansible playbooks
│   ├── inventory/
│   │   └── hosts.yml
│   ├── playbooks/
│   │   ├── setup-k3s.yml       # Установка K3s
│   │   ├── setup-argocd.yml    # Установка ArgoCD
│   │   └── setup-docker.yml    # Установка Docker
│   └── roles/
│       ├── k3s/
│       ├── argocd/
│       └── docker/
│
├── k8s/                          # Kubernetes манифесты
│   ├── base/                     # Базовые манифесты (Kustomize)
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── configmap.yaml
│   │   └── kustomization.yaml
│   └── overlays/                 # Оверлеи для окружений
│       ├── dev/
│       │   └── kustomization.yaml
│       ├── staging/
│       │   └── kustomization.yaml
│       └── prod/
│           └── kustomization.yaml
│
├── argocd/                       # ArgoCD Application манифесты
│   ├── dev-application.yaml
│   ├── staging-application.yaml
│   └── prod-application.yaml
│
├── .github/workflows/            # CI/CD пайплайны
│   ├── ci.yml                   # Build, test, push Docker
│   └── cd.yml                   # Update K8s manifests
│
├── docs/                         # Документация
│   └── setup-guide.md
│
├── .gitignore
├── README.md
├── TECH_STACK.md
└── gitops-cicd-testing-plan.md
```

---

## Почему именно такой стек для VM?

### Terraform
- Декларативное описание инфраструктуры
- Возможность версионировать инфраструктуру
- Легко пересоздать окружение
- Интеграция с Vagrant для локальной разработки

### Ansible
- Agentless - не нужно устанавливать агенты на VM
- Простой YAML синтаксис
- Идемпотентность - можно запускать многократно
- Большая библиотека готовых ролей
- Отлично подходит для установки K3s и ArgoCD

### K3s вместо полного Kubernetes
- **Легковесный**: ~70MB вместо нескольких GB
- **Быстрая установка**: одна команда
- **Меньше ресурсов**: подходит для VM
- **Production-ready**: используется в production
- **Полная совместимость**: 100% Kubernetes API
- **Встроенные компоненты**: containerd, CoreDNS, Traefik

### ArgoCD
- **Web UI**: удобный интерфейс для мониторинга
- **Автоматическая синхронизация**: Git → Cluster
- **Rollback**: откат к предыдущим версиям
- **Multi-cluster support**: управление несколькими кластерами
- **SSO integration**: возможность интеграции с LDAP/OAuth
- **Mature project**: большое сообщество, активная разработка

---

## Workflow

### 1. Подготовка инфраструктуры
```bash
# Создание VM через Vagrant
cd terraform
vagrant up

# Или через Terraform (для cloud providers)
terraform init
terraform plan
terraform apply
```

### 2. Настройка VM
```bash
# Установка K3s, Docker, ArgoCD
cd ansible
ansible-playbook -i inventory/hosts.yml playbooks/setup-all.yml
```

### 3. Разработка приложения
```bash
# Разработка локально
cd app
python app.py

# Коммит изменений
git add .
git commit -m "Add new feature"
git push
```

### 4. CI Pipeline (автоматически)
- GitHub Actions собирает Docker образ
- Запускает тесты
- Публикует образ в registry
- Обновляет image tag в k8s манифестах

### 5. CD через GitOps (автоматически)
- ArgoCD замечает изменения в Git
- Синхронизирует манифесты с кластером
- Деплоит новую версию приложения

---

## Требования к системе

### Локальная машина
- **RAM**: минимум 8GB (рекомендуется 16GB)
- **CPU**: 4+ cores
- **Disk**: 20GB свободного места
- **OS**: Linux, macOS, Windows (WSL2)

### Софт
- Vagrant 2.3+
- VirtualBox 7.0+
- Terraform 1.6+
- Ansible 2.15+
- kubectl 1.28+
- Git 2.40+

### VM конфигурация (для каждой)
- **RAM**: 2-4GB
- **CPU**: 2 cores
- **Disk**: 10GB
- **OS**: Ubuntu 22.04 LTS

---

## Альтернативные варианты

### Если нет ресурсов для VM
- Использовать Docker Desktop + Kind
- Миникуб с меньшими ресурсами

### Если нужно production-like окружение
- Cloud VMs (AWS EC2, GCP Compute Engine, Azure VMs)
- Managed Kubernetes (EKS, GKE, AKS) вместо K3s

### Если нужна простота
- Убрать Terraform, использовать только Vagrant
- Упростить Ansible роли до простых скриптов

---

## Следующие шаги

1. Установить необходимый софт (Vagrant, VirtualBox, Ansible, Terraform)
2. Создать Vagrantfile для локальной VM
3. Написать Ansible playbook для установки K3s
4. Создать простое Flask приложение
5. Настроить GitHub Actions для CI
6. Установить ArgoCD на K3s
7. Настроить GitOps workflow

---

## Полезные ссылки

- [K3s Documentation](https://docs.k3s.io/)
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Vagrant Documentation](https://developer.hashicorp.com/vagrant/docs)
- [Ansible K3s Role](https://github.com/PyratLabs/ansible-role-k3s)
- [Kustomize Documentation](https://kustomize.io/)
