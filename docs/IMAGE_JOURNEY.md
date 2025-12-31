# Путь Docker образа: от feature до production

## Полный жизненный цикл образа

### 📊 Архитектура: Feature → Develop → Staging → Production

```
Developer writes code
         ↓
┌────────────────────────────────────────────────────────────┐
│ STEP 1: Feature Branch                                     │
└────────────────────────────────────────────────────────────┘
         │
         │  git push origin feature/new-api
         ↓
    ┌─────────┐
    │ CI runs │
    └─────────┘
         │
    ✅ Lint, Test, Security
    ✅ BUILD образ → :test (local)
    ✅ Health check
    ❌ PUSH (skipped)
         │
         │  Образ удаляется после CI
         ↓

┌────────────────────────────────────────────────────────────┐
│ STEP 2: Pull Request → develop                            │
└────────────────────────────────────────────────────────────┘
         │
         │  Create PR: feature/new-api → develop
         ↓
    ┌─────────┐
    │ CI runs │  ← На PR ветке (опционально)
    └─────────┘
         │
    ✅ Same checks
    ❌ Still no push
         │
         │  Reviewer approves, merge PR
         ↓

┌────────────────────────────────────────────────────────────┐
│ STEP 3: Develop Branch (First REAL image!)                │
└────────────────────────────────────────────────────────────┘
         │
         │  Merge triggers push to develop
         ↓
    ┌─────────┐
    │ CI runs │
    └─────────┘
         │
    ✅ BUILD образ
    ✅ PUSH → ghcr.io/m2v0a02/gitops:develop-abc123
    ✅ Update k8s/overlays/dev/kustomization.yaml
         │
         ├──────────────────────┐
         │                      │
         ↓                      ↓
    [GHCR Registry]      [Git Repo Updated]
    develop-abc123       newTag: develop-abc123
         │                      │
         │                      ↓
         │              ┌─────────────┐
         │              │   ArgoCD    │
         │              │  (watching) │
         │              └─────────────┘
         │                      │
         │  ◄───────────────────┘ Pull image
         ↓
    ┌─────────────────┐
    │   K8s DEV env   │
    │  Pods running   │
    │  develop-abc123 │
    └─────────────────┘

┌────────────────────────────────────────────────────────────┐
│ STEP 4: Main Branch (Staging/Prod candidate)              │
└────────────────────────────────────────────────────────────┘
         │
         │  Create PR: develop → main
         │  After testing in DEV
         ↓
    ┌─────────┐
    │ CI runs │  ← На PR опционально
    └─────────┘
         │
         │  Merge to main
         ↓
    ┌─────────┐
    │ CI runs │
    └─────────┘
         │
    ✅ BUILD образ (НОВЫЙ!)
    ✅ PUSH → ghcr.io/m2v0a02/gitops:main-xyz789
    ✅ PUSH → ghcr.io/m2v0a02/gitops:latest
    ✅ Update k8s/overlays/staging/kustomization.yaml
         │
         ├──────────────────────┐
         │                      │
         ↓                      ↓
    [GHCR Registry]      [Git Repo Updated]
    main-xyz789          newTag: main-xyz789
    latest = main-xyz789
         │
         │  ⚠️ ArgoCD для staging: MANUAL SYNC
         ↓
    ┌─────────────────┐
    │ K8s STAGING env │
    │ (after manual   │
    │   sync)         │
    └─────────────────┘

┌────────────────────────────────────────────────────────────┐
│ STEP 5: Production Deployment                             │
└────────────────────────────────────────────────────────────┘
         │
         │  Manual approval
         ↓
    ┌──────────────────┐
    │ GitHub Actions   │
    │ Workflow Dispatch│
    │ OR               │
    │ Manual ArgoCD    │
    └──────────────────┘
         │
         ↓
    Update k8s/overlays/prod/kustomization.yaml
    newTag: main-xyz789  ← ТОТ ЖЕ образ что в staging!
         │
         │  ArgoCD MANUAL SYNC
         ↓
    ┌─────────────────┐
    │   K8s PROD env  │
    │  main-xyz789    │
    └─────────────────┘
```

---

## 🔑 Ключевые моменты

### 1. Образ создается ЗАНОВО на каждом этапе?

**Нет!** Важное различие:

| Этап | Что происходит | Результат |
|------|----------------|-----------|
| Feature branch | BUILD образ | ❌ Не сохраняется |
| PR создан | BUILD образ | ❌ Не сохраняется |
| Merge в develop | BUILD + PUSH | ✅ `develop-abc123` |
| Merge в main | BUILD + PUSH | ✅ `main-xyz789` |
| Deploy в staging | — | ✅ Использует `main-xyz789` |
| Deploy в prod | — | ✅ Использует `main-xyz789` |

**Важно**: Образы для develop и main - это **РАЗНЫЕ образы**!

### 2. Почему образы разные?

```bash
# Develop образ
ghcr.io/m2v0a02/gitops:develop-abc123
# Создан из коммита abc123 в develop ветке

# Main образ
ghcr.io/m2v0a02/gitops:main-xyz789
# Создан из коммита xyz789 в main ветке
# xyz789 - это merge commit от develop
```

**Они содержат один и тот же код**, но:
- Разные SHA коммитов
- Разные build timestamps
- Потенциально разные зависимости (если время между build'ами прошло)

### 3. Staging и Production используют ОДИН образ

```
main-xyz789
    ↓
    ├──► Staging (тестирование)
    │
    └──► Production (после approval)
```

**Это важно**: Мы деплоим в production **тот же самый образ**, который протестировали в staging!

---

## 🎯 Детальный пример

### Timeline реального feature

```
День 1: 10:00
├─ Developer: git push origin feature/api-v2
├─ CI: Build :test (local) ❌ не сохраняется
└─ Feature образ удален после CI

День 1: 11:00
├─ Developer: Create PR (feature/api-v2 → develop)
├─ CI: Build :test (local) ❌ не сохраняется
└─ Waiting for review...

День 1: 14:00
├─ Reviewer: Approve & Merge
├─ Git: Merge commit abc123 в develop
└─ CI запускается на develop

День 1: 14:05
├─ CI: BUILD образ
├─ CI: PUSH → ghcr.io/m2v0a02/gitops:develop-abc123 ✅
├─ CI: Update k8s/overlays/dev/kustomization.yaml
│      newTag: develop-abc123
├─ Git: Commit от github-actions[bot]
└─ ArgoCD: Замечает изменение в Git (через ~1 мин)

День 1: 14:07
├─ ArgoCD: Pull образ develop-abc123 из GHCR
├─ ArgoCD: Apply к dev кластеру
└─ DEV: Новая версия работает!

День 2: 10:00 (после тестирования в DEV)
├─ Developer: Create PR (develop → main)
├─ CI на PR: Build :test ❌ не сохраняется
└─ Waiting for approval...

День 2: 15:00
├─ Tech Lead: Approve & Merge to main
├─ Git: Merge commit xyz789 в main
└─ CI запускается на main

День 2: 15:05
├─ CI: BUILD новый образ (из main)
├─ CI: PUSH → ghcr.io/m2v0a02/gitops:main-xyz789 ✅
├─ CI: PUSH → ghcr.io/m2v0a02/gitops:latest ✅
├─ CI: Update k8s/overlays/staging/kustomization.yaml
│      newTag: main-xyz789
└─ Git: Commit от github-actions[bot]

День 2: 15:10
├─ QA Engineer: Manual sync в ArgoCD для staging
├─ ArgoCD: Pull образ main-xyz789 из GHCR
├─ ArgoCD: Apply к staging кластеру
└─ STAGING: Тестирование новой версии

День 3: 10:00 (после тестирования в STAGING)
├─ Tech Lead: Approve production deploy
├─ DevOps: Run workflow "CD - Deploy to Production"
│          Input: main-xyz789
├─ Workflow: Update k8s/overlays/prod/kustomization.yaml
│           newTag: main-xyz789  ← ТОТ ЖЕ образ!
└─ Git: Commit "Deploy to production: main-xyz789"

День 3: 10:05
├─ DevOps: Manual sync в ArgoCD для prod
├─ ArgoCD: Pull образ main-xyz789 из GHCR
│          (уже в cache, был протестирован в staging)
├─ ArgoCD: Apply к prod кластеру
└─ PRODUCTION: Новая версия в production! 🚀
```

---

## 🔄 Сколько раз билдится образ?

Для одного feature:

```
Feature branch:  1 раз (не сохраняется)
PR to develop:   1 раз (не сохраняется)
Merge to develop: 1 раз (сохраняется ✅ develop-abc123)
PR to main:      1 раз (не сохраняется)
Merge to main:   1 раз (сохраняется ✅ main-xyz789)
────────────────────────────────────────────────────
TOTAL: 5 builds, 2 образа в registry
```

---

## 🎭 Разные стратегии

### Стратегия 1: Current (Build каждый раз)

**Что происходит**:
- Develop: BUILD новый образ
- Main: BUILD новый образ
- Staging: Использует main образ
- Prod: Использует main образ

**Плюсы**:
- ✅ Всегда свежие зависимости
- ✅ Проще понять (каждая ветка = свой образ)

**Минусы**:
- ❌ Дублирование работы (build 2 раза для одного кода)
- ❌ Staging может тестировать чуть другой образ чем dev

### Стратегия 2: Promote Image (рекомендуется для production)

**Что происходит**:
- Develop: BUILD образ → `develop-abc123`
- Main: НЕ билдит, а ре-тегает → `main = develop-abc123`
- Staging: Использует `main` (= `develop-abc123`)
- Prod: Использует `main` (= `develop-abc123`)

**Плюсы**:
- ✅ Точно тот же образ через все окружения
- ✅ Быстрее (1 build вместо 2)
- ✅ Гарантия: prod = то что тестировали в dev

**Минусы**:
- ❌ Сложнее настроить workflow
- ❌ Нужны дополнительные проверки

**Пример workflow**:
```yaml
# Вместо build на main
- name: Promote develop image to main
  run: |
    # Pull develop образ
    docker pull ghcr.io/m2v0a02/gitops:develop-${{ github.sha }}

    # Re-tag как main
    docker tag ghcr.io/m2v0a02/gitops:develop-${{ github.sha }} \
               ghcr.io/m2v0a02/gitops:main-${{ github.sha }}
    docker tag ghcr.io/m2v0a02/gitops:develop-${{ github.sha }} \
               ghcr.io/m2v0a02/gitops:latest

    # Push
    docker push ghcr.io/m2v0a02/gitops:main-${{ github.sha }}
    docker push ghcr.io/m2v0a02/gitops:latest
```

### Стратегия 3: Immutable Tags (enterprise)

**Что происходит**:
- Build один раз с digest
- Все окружения используют digest, не tag

```yaml
# Вместо тегов
images:
  - name: gitops-demo-app
    newName: ghcr.io/m2v0a02/gitops
    digest: sha256:abc123...  # ← Immutable!
```

---

## 📦 Что находится в образе?

```dockerfile
# Snapshot момента build:
├── Python 3.11 (base image)
├── Flask 3.0.0
├── Werkzeug 3.0.1
├── prometheus-client 0.19.0
├── gunicorn 21.2.0
├── app.py (ваш код)
└── Metadata:
    ├── Created: 2025-12-31T15:05:00Z
    ├── Git SHA: xyz789
    └── Labels: version, branch, etc.
```

**Важно**: Если между build'ами обновился Python или зависимости, образы будут разные!

---

## 🚀 Production Deployment Flow

### Manual Approach (текущая)

```bash
# 1. Определить какой образ деплоить
IMAGE_TAG="main-xyz789"

# 2. Update prod manifest
cd k8s/overlays/prod
yq eval ".images[0].newTag = \"$IMAGE_TAG\"" -i kustomization.yaml

# 3. Commit
git add kustomization.yaml
git commit -m "Deploy $IMAGE_TAG to production"
git push

# 4. ArgoCD manual sync
# UI → prod application → SYNC
```

### GitHub Actions Workflow (включено)

```bash
# GitHub UI → Actions → "CD - Deploy to Production"
# Input: main-xyz789
# Button: Run workflow
```

```yaml
# .github/workflows/cd-prod.yaml
- run: |
    yq eval '.images[0].newTag = "${{ inputs.image-tag }}"' \
      -i k8s/overlays/prod/kustomization.yaml
    git commit -am "Deploy to production: ${{ inputs.image-tag }}"
    git push
```

### GitOps Flow

```
GitHub Workflow
    ↓
Git commit (prod manifest updated)
    ↓
ArgoCD detects change
    ↓
Manual sync required (safety)
    ↓
ArgoCD pulls image
    ↓
ArgoCD applies to K8s
    ↓
Pods rolling update
    ↓
Production updated! 🎉
```

---

## 🔍 Как убедиться что образ одинаковый?

### Image Digest

```bash
# Посмотреть digest образа
docker inspect ghcr.io/m2v0a02/gitops:main-xyz789 | jq '.[0].RepoDigests'

# Результат:
[
  "ghcr.io/m2v0a02/gitops@sha256:8e73fc88a30caa0e2f0d7f6935811a256d4f9c1598e15a4235392c8e2b6c329c"
]
```

**Digest** - это SHA256 hash содержимого образа.

**Если digest одинаковый = образы идентичны!**

### В Kubernetes

```bash
# Посмотреть какой образ используется
kubectl get pod -n prod -o jsonpath='{.items[0].spec.containers[0].image}'

# Результат:
ghcr.io/m2v0a02/gitops:main-xyz789

# Посмотреть реальный digest
kubectl get pod -n prod -o jsonpath='{.items[0].status.containerStatuses[0].imageID}'

# Результат:
ghcr.io/m2v0a02/gitops@sha256:8e73fc88...
```

---

## 📊 Summary: Image Flow

```
┌──────────────┐
│ Feature      │ → Build :test → 🗑️ Deleted
└──────────────┘

┌──────────────┐
│ PR           │ → Build :test → 🗑️ Deleted
└──────────────┘

┌──────────────┐                    ┌──────────┐
│ Develop      │ → Build & Push → │ GHCR     │
└──────────────┘                    │ develop- │
                                    │ abc123   │
                                    └────┬─────┘
                                         │
                                         ↓
                                    ┌──────────┐
                                    │ DEV K8s  │
                                    └──────────┘

┌──────────────┐                    ┌──────────┐
│ Main         │ → Build & Push → │ GHCR     │
└──────────────┘                    │ main-    │
                                    │ xyz789   │
                                    └────┬─────┘
                                         │
                    ┌────────────────────┼────────────────┐
                    ↓                    ↓                ↓
               ┌──────────┐         ┌─────────┐    ┌─────────┐
               │ STAGING  │         │  PROD   │    │ Latest  │
               │   K8s    │         │   K8s   │    │  tag    │
               └──────────┘         └─────────┘    └─────────┘
                 Manual               Manual
                  Sync                 Sync
```

---

## ✅ Best Practices для Production

### 1. Semantic Versioning

```bash
# Вместо SHA, используйте semver
git tag v1.2.3
git push --tags

# CI создаст:
ghcr.io/m2v0a02/gitops:v1.2.3
ghcr.io/m2v0a02/gitops:1.2
ghcr.io/m2v0a02/gitops:1
ghcr.io/m2v0a02/gitops:latest
```

### 2. Image Promotion

```yaml
# Promote вместо rebuild
dev → staging → prod
(один образ через все окружения)
```

### 3. Approval Gates

```yaml
# GitHub Environments с required reviewers
environments:
  production:
    required_reviewers: [tech-lead, devops]
```

### 4. Rollback Strategy

```bash
# Сохранять N последних версий
# В prod manifest храните историю:
# Current: main-xyz789
# Previous: main-abc123 (comment)
# Rollback: просто раскоментировать
```

---

## 🎯 Ответ на ваш вопрос

**"Как образ доставляется в prod?"**

1. **Feature branch**: Build локально → удаляется
2. **Merge в develop**: Build → Push `develop-abc123` → DEV
3. **Merge в main**: Build → Push `main-xyz789` → STAGING (manual)
4. **Production deploy**:
   - ❌ НЕ создается новый образ
   - ✅ Используется `main-xyz789` (тот же что в staging)
   - Manual sync в ArgoCD или GitHub workflow
   - ArgoCD pulls образ из GHCR
   - ArgoCD деплоит в prod кластер

**Ключевой момент**: Production использует образ созданный при merge в main, который уже протестирован в staging!
