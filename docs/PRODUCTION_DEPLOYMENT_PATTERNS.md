# Production Deployment Patterns в больших компаниях

## Паттерн 1: Git Tags (самый популярный)

### Используется в: Google, Netflix, Spotify, Uber

```
┌────────────────────────────────────────────────────────────────┐
│  DEVELOPMENT → STAGING → PRODUCTION                            │
└────────────────────────────────────────────────────────────────┘

Week 1: Development
─────────────────────
Developer: git push develop
  ↓
CI: автоматически обновляет dev/kustomization.yaml
  newTag: develop-abc123  ← SHA-based
  ↓
ArgoCD Dev: auto-sync ✅

Week 2: Release to Staging
──────────────────────────
git checkout main
git merge develop
git tag v1.2.3  ← РЕЛИЗ ТЕГ
git push origin v1.2.3
  ↓
CI on tag:
  - Собирает RELEASE образ: v1.2.3
  - Обновляет staging/kustomization.yaml:
    newTag: v1.2.3  ← ВЕРСИЯ, не SHA!
  ↓
ArgoCD Staging: manual sync (SRE нажимает кнопку)

Week 3: Production
──────────────────
SRE вручную:
  cd k8s/overlays/prod
  vim kustomization.yaml
  # newTag: v1.2.3  ← Та же версия что в staging!
  git commit -m "Deploy v1.2.3 to production"
  git push
  ↓
ArgoCD Production: manual sync + approval
  ↓
Production: v1.2.3 deployed ✅
```

### Конфигурация:

```yaml
# .github/workflows/release.yaml
name: Release

on:
  push:
    tags:
      - 'v*.*.*'

jobs:
  release:
    steps:
      - name: Build release image
        run: docker build -t ghcr.io/company/app:${{ github.ref_name }}

      - name: Push release image
        run: docker push ghcr.io/company/app:${{ github.ref_name }}

      - name: Update staging manifest
        run: |
          cd k8s/overlays/staging
          yq eval '.images[0].newTag = "${{ github.ref_name }}"' -i kustomization.yaml
          git commit -m "Release ${{ github.ref_name }} to staging"
          git push

      - name: Create production PR
        run: |
          # Создать PR для production с тем же тегом
          # Требует manual approval
```

---

## Паттерн 2: Immutable SHA + Promotion (Google/Uber стиль)

### Одна сборка → все окружения

```
┌────────────────────────────────────────────────────────────────┐
│  ОДИН ОБРАЗ ПРОХОДИТ ЧЕРЕЗ ВСЕ ОКРУЖЕНИЯ                       │
└────────────────────────────────────────────────────────────────┘

Сборка:
  Commit: abc123
  Image: sha256:1a2b3c4d5e6f (digest)
  Tag: main-abc123

  ↓ Деплой в Dev (автоматически)

Dev Environment:
  newTag: main-abc123
  Testing: ✅ Pass

  ↓ Promotion в Staging (автоматически после тестов)

Staging Environment:
  newTag: main-abc123  ← ТОТ ЖЕ образ!
  Testing: ✅ Pass

  ↓ Promotion в Production (вручную)

Production Environment:
  newTag: main-abc123  ← ТОТ ЖЕ образ!
  Status: ✅ Deployed
```

### Автоматическая промоция:

```yaml
# .github/workflows/promote.yaml
name: Promote to next environment

on:
  workflow_dispatch:
    inputs:
      image_tag:
        description: 'Image tag to promote (e.g., main-abc123)'
        required: true
      from_env:
        description: 'Source environment'
        required: true
        type: choice
        options: [dev, staging]
      to_env:
        description: 'Target environment'
        required: true
        type: choice
        options: [staging, production]

jobs:
  promote:
    steps:
      - name: Verify image in source env
        run: |
          # Проверить что образ работает в source env
          kubectl get deployment -n ${{ inputs.from_env }}

      - name: Update target environment
        run: |
          cd k8s/overlays/${{ inputs.to_env }}
          yq eval '.images[0].newTag = "${{ inputs.image_tag }}"' -i kustomization.yaml
          git commit -m "Promote ${{ inputs.image_tag }} to ${{ inputs.to_env }}"

      - name: Create PR for approval
        if: inputs.to_env == 'production'
        run: gh pr create --title "Deploy to production: ${{ inputs.image_tag }}"
```

---

## Паттерн 3: Separate Config Repository (Netflix стиль)

### Application repo vs Config repo

```
┌────────────────────────────────────────────────────────────────┐
│  APPLICATION REPOSITORY                                        │
│  github.com/company/service-api                                │
│                                                                │
│  CI автоматически:                                             │
│  - Build image: service-api:main-abc123                        │
│  - Push to registry                                            │
│  - НЕ обновляет никакие манифесты                              │
└────────────────────────────────────────────────────────────────┘
                            │
                            │ CI triggers webhook
                            ↓
┌────────────────────────────────────────────────────────────────┐
│  CONFIG REPOSITORY (отдельный!)                                │
│  github.com/company/infrastructure                             │
│                                                                │
│  Branches:                                                     │
│  ├── dev        → ArgoCD dev cluster                          │
│  ├── staging    → ArgoCD staging cluster                      │
│  └── production → ArgoCD production cluster                   │
│                                                                │
│  Обновление:                                                   │
│  - Dev: автоматически через PR от CI                          │
│  - Staging: вручную (DevOps approve PR)                       │
│  - Production: вручную (SRE + Manager approve)                │
└────────────────────────────────────────────────────────────────┘
```

### Automatic PR creation:

```yaml
# В app repo: .github/workflows/ci.yaml
jobs:
  update-dev-config:
    steps:
      - name: Checkout config repo
        uses: actions/checkout@v4
        with:
          repository: company/infrastructure
          token: ${{ secrets.CONFIG_REPO_TOKEN }}

      - name: Update dev config
        run: |
          cd environments/dev/service-api
          yq eval '.image.tag = "${{ github.sha }}"' -i values.yaml

      - name: Create PR
        run: |
          git checkout -b update-service-api-dev-${{ github.sha }}
          git commit -am "Update service-api dev to ${{ github.sha }}"
          git push origin update-service-api-dev-${{ github.sha }}
          gh pr create --title "Update service-api dev" --auto-merge
          # Auto-merge для dev, но не для staging/prod!
```

---

## Паттерн 4: ArgoCD Image Updater (автоматизация)

### Используется в: Shopify, GitLab

ArgoCD Image Updater - отдельный компонент, который автоматически обновляет теги.

```yaml
# argocd-image-updater ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-image-updater-config
data:
  applications: |
    - name: service-api-dev
      image: ghcr.io/company/service-api
      update-strategy: latest  # Автоматически latest для dev

    - name: service-api-staging
      image: ghcr.io/company/service-api
      update-strategy: semver  # Только semver теги (v1.2.3)
      semver-constraint: ^1.0  # Major version 1.x

    - name: service-api-prod
      image: ghcr.io/company/service-api
      update-strategy: digest  # Только явно указанный digest
      # Не обновляется автоматически!
```

---

## Паттерн 5: Blue-Green with Manual Switch (Amazon стиль)

### Два полных environment в production

```
Production Cluster:
├── blue/  (текущая версия v1.2.3)
│   ├── deployment (100% traffic)
│   └── service
└── green/ (новая версия v1.3.0)
    ├── deployment (0% traffic)
    └── service

Деплой процесс:
1. Deploy v1.3.0 в green environment
2. Smoke tests на green
3. SRE вручную переключает traffic:
   - 0% blue, 100% green (instant)
   - Или gradual: 90/10, 80/20, ... 0/100
4. Monitor metrics
5. Если проблемы: instant rollback (switch back to blue)
```

```yaml
# prod/kustomization.yaml
# SRE меняет вручную:

# Before:
patchesStrategicMerge:
  - blue-traffic-100.yaml   # 100% на blue
  - green-traffic-0.yaml    # 0% на green

# After deployment verification:
patchesStrategicMerge:
  - blue-traffic-0.yaml     # 0% на blue
  - green-traffic-100.yaml  # 100% на green
```

---

## Сравнение подходов в больших компаниях

| Компания | Подход | Dev | Staging | Production |
|----------|--------|-----|---------|------------|
| **Google** | Mono-repo + SHA tags | Auto | Auto (after tests) | Manual (SRE) |
| **Netflix** | Multi-repo + Spinnaker | Auto PR | Manual merge | Manual + Canary |
| **Uber** | SHA promotion | Auto | Auto (after tests) | Manual (2 approvals) |
| **Spotify** | Squad repos + GitOps | Auto | Manual | Manual + AB test |
| **Amazon** | Service repos + Blue/Green | Auto | Manual | Manual switch |
| **GitLab** | ArgoCD Image Updater | Auto (latest) | Auto (semver) | Manual (digest) |

---

## Общие паттерны для Production:

### 1. ✅ Git Tags для релизов

```bash
# Все используют semver
git tag v1.2.3
git push origin v1.2.3

# Production использует только tagged версии
prod/kustomization.yaml:
  newTag: v1.2.3  # Не SHA!
```

### 2. ✅ Manual Approval для Production

```yaml
# GitHub Environment Protection Rules
environments:
  production:
    protection_rules:
      - required_reviewers: 2
      - wait_timer: 300  # 5 минут на размышление
      - deployment_branch_policy:
          protected_branches: true
```

### 3. ✅ Один образ → все окружения

```
Build один раз: main-abc123
  ↓
Dev:     main-abc123 (сразу)
  ↓
Staging: main-abc123 (после тестов)
  ↓
Prod:    main-abc123 (после approval)

ВСЕ используют ОДИНАКОВЫЙ образ!
```

### 4. ✅ Immutable tags

```bash
# ❌ ПЛОХО (для production)
newTag: latest
newTag: develop

# ✅ ХОРОШО
newTag: v1.2.3
newTag: main-abc123456...  # Full SHA
newTag: sha256:1a2b3c4d...  # Digest
```

### 5. ✅ Separate ArgoCD Projects

```yaml
# argocd-projects.yaml

# Dev project - автоматический
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: dev
spec:
  syncWindows:
    - kind: allow
      schedule: '* * * * *'  # Всегда можно деплоить

# Production project - ограниченный
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: production
spec:
  syncWindows:
    - kind: deny
      schedule: '0 22 * * 5-6'  # Нельзя в пятницу вечером!
      duration: 48h
  destinations:
    - namespace: production
      server: https://prod-cluster
  roles:
    - name: deploy
      policies:
        - p, proj:production:deploy, applications, sync, production/*, allow
      groups:
        - sre-team  # Только SRE могут деплоить
```

---

## 🎯 Ваша текущая конфигурация vs Большие компании

### Что у вас уже правильно:

```diff
✅ Dev: auto-sync
✅ Staging/Prod: manual sync
✅ Разные ветки: develop vs main
✅ SHA-based теги: develop-abc123

Что делают большие компании:
+ Git tags для релизов (v1.2.3)
+ Deployment windows (не деплоить в пятницу!)
+ Rollback план в каждом PR
+ Metrics verification перед production
+ Gradual rollout (canary, blue-green)
```

---

## Рекомендации для вашего проекта:

### Сейчас (обучение):
✅ Оставить как есть:
- Dev: auto-sync с SHA тегами
- Prod: manual sync

### Перед реальным production:
✅ Добавить git tags:
```bash
git tag v1.0.0
git push origin v1.0.0

# Update prod to use tags, not branches
prod-application.yaml:
  targetRevision: v1.0.0  # Вместо "main"
```

### Для роста (если проект растет):
✅ Рассмотреть:
- ArgoCD Image Updater
- Separate config repository
- Blue-Green deployments
- Canary releases

---

## Пример: Как Netflix делает production deploy

```
1. Developer: git push origin main
   ↓
2. CI (Spinnaker):
   - Build image: service:main-abc123
   - Push to registry
   - Run tests
   ↓
3. Auto-deploy to Dev cluster (100 instances)
   - Automated tests
   - Canary analysis (5% traffic)
   ↓
4. Auto-promote to Staging (если canary ok)
   - Full regression tests
   - Load testing
   ↓
5. Manual approval (SRE + Product Manager)
   - Review metrics
   - Check error rates
   - Approve or Reject
   ↓
6. Production deploy:
   - Blue-Green switch
   - Gradual rollout: 1% → 5% → 25% → 50% → 100%
   - Automated rollback если error rate > threshold
   ↓
7. Post-deploy:
   - Monitor dashboards
   - Alert on-call if issues
   - Automatic rollback если проблемы
```

---

## Итого: Да, вы правильно поняли!

✅ **Dev**: CI автоматически меняет SHA → ArgoCD автоматически деплоит

✅ **Production**:
- Вручную указывают тег (v1.2.3)
- Вручную approve PR
- Вручную запускают sync
- Вручную мониторят результат

✅ **Большие компании делают так же**, только добавляют:
- Git tags вместо SHA для релизов
- Automated testing между окружениями
- Gradual rollout (canary, blue-green)
- Automated rollback при проблемах
- Deployment windows (не деплоить в пятницу!)

Ваша текущая конфигурация - это **правильная основа**! 🎉
