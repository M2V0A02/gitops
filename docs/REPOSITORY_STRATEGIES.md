# GitOps Repository Strategies для Production

## Рекомендация для вашего проекта: Enhanced Mono-repo

### Текущая ситуация
✅ У вас уже mono-repo с правильной структурой
✅ ArgoCD настроен на разные ветки для разных сред
✅ Manual sync для staging и prod

### Что нужно добавить для Production:

## 1. GitHub Branch Protection Rules

### Protect `main` branch:
```yaml
Settings → Branches → Branch protection rules

Rule for: main
  ☑ Require pull request reviews before merging
    - Required approving reviews: 2
    - Dismiss stale reviews when new commits are pushed

  ☑ Require status checks to pass before merging
    - CI Pipeline
    - Security Scan
    - Tests

  ☑ Require conversation resolution before merging

  ☑ Restrict who can push to matching branches
    - Add: DevOps team
    - Add: Platform team

  ☑ Allow force pushes: NO
  ☑ Allow deletions: NO
```

### Protect production manifests with CODEOWNERS:
```bash
# Create .github/CODEOWNERS
cat > .github/CODEOWNERS << 'EOF'
# Production manifests require SRE approval
/k8s/overlays/prod/        @company/sre-team
/k8s/overlays/staging/     @company/devops-team

# Application code - all developers can review
/app/                      @company/developers

# CI/CD changes require DevOps approval
/.github/workflows/        @company/devops-team

# ArgoCD apps require Platform team approval
/argocd/                   @company/platform-team
EOF
```

---

## 2. Separate Directories with Clear Ownership

```
gitops/
├── app/                          ← Developers own
│   ├── app.py
│   └── Dockerfile
│
├── k8s/
│   ├── base/                     ← Shared, Platform team owns
│   └── overlays/
│       ├── dev/                  ← Developers can change
│       │   └── kustomization.yaml
│       ├── staging/              ← DevOps approval required
│       │   └── kustomization.yaml
│       └── prod/                 ← SRE team ONLY
│           └── kustomization.yaml
│
└── .github/
    └── workflows/
        ├── ci.yaml               ← DevOps owns
        └── cd-prod.yaml          ← SRE owns
```

---

## 3. Git Tags для Production Releases

### Workflow:
```bash
# After successful staging deployment
git checkout main
git tag -a v1.2.3 -m "Release v1.2.3: Add user API"
git push origin v1.2.3
```

### Update prod-application.yaml to use tags:
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: gitops-demo-prod
spec:
  source:
    repoURL: https://github.com/M2V0A02/gitops.git
    targetRevision: v1.2.3  # ← Use tag instead of branch
    path: k8s/overlays/prod
```

**Преимущества**:
- Immutable releases
- Clear version history
- Easy rollback: change tag to previous version
- Production никогда не следует за "latest" в main

---

## 4. ArgoCD RBAC для разных команд

```yaml
# argocd-rbac-cm ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-rbac-cm
  namespace: argocd
data:
  policy.default: role:readonly

  policy.csv: |
    # Developers: full access to dev, readonly to staging
    p, role:developer, applications, *, dev/*, allow
    p, role:developer, applications, get, staging/*, allow

    # DevOps: full access to dev and staging
    p, role:devops, applications, *, dev/*, allow
    p, role:devops, applications, *, staging/*, allow
    p, role:devops, applications, get, prod/*, allow

    # SRE: full access to everything
    p, role:sre, applications, *, */*, allow

    # Groups
    g, developers, role:developer
    g, devops-team, role:devops
    g, sre-team, role:sre
```

---

## 5. Separate CI/CD Workflows

### ci.yaml - для develop branch
```yaml
name: CI - Dev Environment
on:
  push:
    branches: [develop]

jobs:
  deploy-dev:
    # Build, push, update dev manifests
```

### cd-staging.yaml - для main branch
```yaml
name: CD - Staging
on:
  push:
    branches: [main]

jobs:
  deploy-staging:
    # Build, push, update staging manifests
    # Notify team in Slack
```

### cd-prod.yaml - manual trigger only
```yaml
name: CD - Production
on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Git tag to deploy (e.g., v1.2.3)'
        required: true

jobs:
  deploy-prod:
    environment: production  # Requires GitHub Environment approval
    steps:
      - name: Update prod manifest to tag ${{ inputs.version }}
      - name: Create deployment PR
      - name: Wait for approval
      - name: Notify on-call team
```

---

## 6. Audit Logging

### Enable ArgoCD audit logs:
```yaml
# argocd-cm ConfigMap
data:
  application.instanceLabelKey: argocd.argoproj.io/instance
  audit.enabled: "true"
  audit.logFormat: json
```

### Git commit messages for production:
```bash
git commit -m "prod: Deploy v1.2.3

- Approved by: @john-doe
- Ticket: JIRA-1234
- Tested in staging: 2024-12-31
- Rollback plan: Revert to v1.2.2
"
```

---

## Когда переходить на Multi-repo?

### Признаки что нужен Multi-repo:

1. **Команда > 20 человек**
   - Сложно управлять permissions в mono-repo

2. **Много микросервисов**
   - У вас 10+ приложений в одном репо
   - Каждое со своими манифестами

3. **Строгие compliance требования**
   - PCI-DSS, SOC2, ISO 27001
   - Нужен полный audit trail для prod

4. **Разные команды владеют разными сервисами**
   - Team A не должен видеть config Team B

5. **Multi-cluster deployment**
   - Dev cluster, Staging cluster, Prod cluster
   - Разные Kubernetes версии

### Если НЕТ этих признаков → Mono-repo достаточно!

---

## Hybrid подход (рекомендуется для роста)

```
Начало (1-10 человек):
  ✅ Mono-repo с branch protection

Рост (10-50 человек):
  ✅ Mono-repo + CODEOWNERS + RBAC

Масштаб (50+ человек):
  ✅ Multi-repo:
     - App repos (по команде)
     - Config repo (централизованный)
```

---

## Примеры из индустрии

### Mono-repo используют:
- **Google**: весь код в одном mega-repo
- **Facebook**: mono-repo для большинства сервисов
- **Uber**: mono-repo для Go сервисов

### Multi-repo используют:
- **Netflix**: тысячи микросервисов, отдельные репо
- **Amazon**: каждый сервис = отдельный репо
- **Spotify**: squad-based repos

---

## Ваша ситуация: Что делать?

### Сейчас (Обучение/MVP):
✅ **Оставить mono-repo**
- Добавить branch protection на main
- Добавить CODEOWNERS для k8s/overlays/prod/
- Использовать manual sync для prod

### Перед production запуском:
✅ **Enhanced mono-repo**
- GitHub branch protection rules
- CODEOWNERS файл
- ArgoCD RBAC
- Git tags для releases
- Separate workflows для prod

### Если проект растет (>20 человек):
✅ **Рассмотреть multi-repo**
- Отдельный config repo
- App repos по командам
- Centralized ArgoCD

---

## Quick Decision Matrix

| Критерий | Mono-repo | Multi-repo |
|----------|-----------|------------|
| Размер команды | < 20 | > 20 |
| Количество сервисов | 1-5 | 10+ |
| Compliance требования | Low/Medium | High |
| DevOps зрелость | Low/Medium | High |
| Время на setup | 1 день | 1 неделя |
| Complexity | Low | High |

---

## Рекомендация для вас:

### ✅ Используйте Enhanced Mono-repo

**Причины**:
1. Вы учитесь GitOps (простота важна)
2. Один сервис (пока)
3. Маленькая команда
4. Уже настроено правильно

**Что добавить**:
1. Branch protection rules для main
2. CODEOWNERS файл
3. Git tags для production releases
4. Manual workflow для prod deploy

**Переход на multi-repo**:
- Только когда команда > 20 человек
- Или когда > 10 микросервисов
- Или compliance требует

---

## Пример конфигурации для вашего проекта:

```bash
# 1. Add branch protection (через GitHub UI)
# 2. Create CODEOWNERS
cat > .github/CODEOWNERS << 'EOF'
# Production requires SRE approval
/k8s/overlays/prod/     @M2V0A02

# Staging requires review
/k8s/overlays/staging/  @M2V0A02

# Dev - anyone can change
/k8s/overlays/dev/      @M2V0A02
EOF

# 3. Use tags for prod
git tag v1.0.0
git push origin v1.0.0

# 4. Update prod app to use tags
vim argocd/prod-application.yaml
# targetRevision: v1.0.0  (instead of 'main')
```

---

## Итого:

**Для production mono-repo достаточно при условии**:
✅ Branch protection
✅ CODEOWNERS
✅ Manual sync для prod
✅ Git tags для releases
✅ Proper RBAC в ArgoCD

**Multi-repo нужен только если**:
- Большая команда (>20)
- Много сервисов (>10)
- Строгие compliance требования
- Multi-cluster deployment
