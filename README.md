# GitOps и CI/CD Testing Project

Проект для изучения и тестирования GitOps принципов и CI/CD пайплайнов.

## Описание

Этот проект создан для практического освоения современных DevOps практик:
- Continuous Integration (CI)
- Continuous Deployment (CD)
- GitOps подход к управлению инфраструктурой
- Декларативное управление Kubernetes ресурсами

## Структура проекта

```
.
├── app/                          # Flask приложение
├── terraform/                    # Terraform для VM
├── ansible/                      # Ansible playbooks (K3s, ArgoCD)
├── k8s/                          # Kubernetes манифесты
│   ├── base/                     # Базовые манифесты
│   └── overlays/                 # Кастомизация для окружений
│       ├── dev/                  # Development окружение
│       ├── staging/              # Staging окружение
│       └── prod/                 # Production окружение
├── argocd/                       # ArgoCD Applications
├── .github/workflows/            # GitHub Actions CI/CD пайплайны
└── docs/                         # Документация
```

## Технологический стек

### Инфраструктура:
- **Platform**: Virtual Machines (Vagrant + VirtualBox)
- **Provisioning**: Terraform
- **Configuration**: Ansible
- **Kubernetes**: K3s (легковесный дистрибутив)

### Приложение и CI/CD:
- **Application**: Python Flask
- **Containerization**: Docker
- **CI**: GitHub Actions
- **Container Registry**: Docker Hub / GitHub Container Registry
- **GitOps**: ArgoCD
- **Manifest Management**: Kustomize

## Текущий статус

- [x] Инициализация Git репозитория
- [x] Создание базовой структуры директорий
- [x] Настройка .gitignore
- [x] Создание README.md
- [x] Выбор технологического стека
- [ ] Создание тестового Flask приложения
- [ ] Настройка Vagrant + VM
- [ ] Создание Ansible playbooks
- [ ] Настройка CI пайплайна
- [ ] Установка K3s и ArgoCD
- [ ] Внедрение GitOps workflow

## Начало работы

Следуйте шагам из [gitops-cicd-testing-plan.md](./gitops-cicd-testing-plan.md) для поэтапной настройки проекта.

## Цели обучения

1. Понять принципы GitOps
2. Настроить автоматизированный CI/CD пайплайн
3. Научиться управлять Kubernetes манифестами декларативно
4. Освоить инструменты для непрерывной доставки
5. Практиковать Infrastructure as Code (IaC)

## Документация

- [План тестирования](./gitops-cicd-testing-plan.md) - полный план с чеклистами
- [Технологический стек](./TECH_STACK.md) - детальное описание выбранных технологий и архитектуры

## Лицензия

Учебный проект для личного использования.
