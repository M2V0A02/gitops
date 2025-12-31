# Docker Image Lifecycle и Storage Strategy

## Когда CI создает образ?

### 🔨 BUILD vs PUSH - Важное различие!

```yaml
# Job 4: Build Docker Image
build:
  runs-on: ubuntu-latest
  needs: [lint, security, test]
  # ⚠️ БЕЗ условий - запускается ВСЕГДА для ВСЕХ веток!

# Job 5: Push Docker Image
push:
  needs: build
  if: github.event_name == 'push' && (github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop')
  # ✅ ТОЛЬКО для main и develop веток!
```

### Поведение по веткам

| Ветка | Build образ? | Push в registry? | Где хранится? |
|-------|-------------|------------------|---------------|
| `feature/*` | ✅ Да | ❌ Нет | CI cache only |
| `develop` | ✅ Да | ✅ Да | ghcr.io |
| `main` | ✅ Да | ✅ Да | ghcr.io |
| PR | ✅ Да | ❌ Нет | CI cache only |

---

## Что происходит с feature ветками?

### Пример: `feature/new-api`

```
Developer pushes to feature/new-api
         ↓
┌─────────────────────┐
│ CI Pipeline         │
├─────────────────────┤
│ ✅ Lint            │
│ ✅ Security        │
│ ✅ Test            │
│ ✅ BUILD образ     │ ← Образ создается!
│    └─ test local   │ ← Тестируется локально в CI
│    └─ health check │
│ ❌ PUSH (skipped)  │ ← НЕ публикуется в registry
└─────────────────────┘
         ↓
Образ удаляется после завершения CI
(но остается в GitHub Actions cache)
```

### Зачем билдить если не пушить?

1. **Проверка сборки** - убедиться что Dockerfile корректен
2. **Тестирование образа** - запустить контейнер и проверить health
3. **Fail fast** - найти проблемы ДО merge в main/develop
4. **PR validation** - блокировать merge если образ не собирается

---

## GitHub Actions Cache

### Docker Layer Caching

```yaml
- uses: docker/build-push-action@v5
  with:
    cache-from: type=gha          # ← Читает из cache
    cache-to: type=gha,mode=max   # ← Пишет в cache
```

**Что кешируется**:
- Docker layers (базовые образы, зависимости)
- Pip packages
- Build artifacts

**Retention**: 7 дней неактивности

**Размер**: До 10GB на репозиторий

**Преимущество**: Ускорение сборки в 2-5 раз

---

## Хранение образов в Registry

### Текущая стратегия (только main/develop)

```
ghcr.io/m2v0a02/gitops/
├── latest              # main HEAD
├── main                # main HEAD
├── main-dc927a4        # коммит 1
├── main-b2aeb07        # коммит 2
├── main-b2b50f7        # коммит 3
├── develop             # develop HEAD
├── develop-abc123      # коммит 1
└── develop-xyz789      # коммит 2
```

**Проблема**: Быстро растет количество образов!

---

## Storage Strategies для Production

### Стратегия 1: Минимальная (текущая)

**Что пушится**:
- Только `main` и `develop`

**Плюсы**:
- ✅ Минимальное хранилище
- ✅ Простая настройка
- ✅ Нет мусора от feature веток

**Минусы**:
- ❌ Нельзя протестировать feature образ в реальном окружении
- ❌ Нельзя поделиться образом с коллегами

### Стратегия 2: Feature Branches on Demand

```yaml
# Пушить только при наличии label "push-image"
if: |
  github.event_name == 'push' && (
    github.ref == 'refs/heads/main' ||
    github.ref == 'refs/heads/develop' ||
    contains(github.event.pull_request.labels.*.name, 'push-image')
  )
```

**Плюсы**:
- ✅ Контролируемое создание образов
- ✅ Можно протестировать важные features

**Минусы**:
- ❌ Нужно вручную добавлять label

### Стратегия 3: All Branches + Cleanup

```yaml
# Push все ветки
if: github.event_name == 'push'

# Но добавить cleanup job
- name: Delete old images
  run: |
    # Удалить образы старше 7 дней
    # Кроме main, develop, и tagged releases
```

**Плюсы**:
- ✅ Максимальная гибкость
- ✅ Любую ветку можно задеплоить

**Минусы**:
- ❌ Требует автоматическую очистку
- ❌ Больше хранилища

### Стратегия 4: Pull Requests Only

```yaml
# Пушить только для PR в main/develop
if: |
  github.event_name == 'pull_request' &&
  (github.base_ref == 'main' || github.base_ref == 'develop')

# Тег: pr-123
tags: pr-${{ github.event.pull_request.number }}
```

**Плюсы**:
- ✅ Образы для review
- ✅ QA может протестировать
- ✅ Автоматически связано с PR

**Минусы**:
- ❌ Образы остаются после merge PR

---

## Recommended Strategy для вашего проекта

### Вариант A: Hybrid (рекомендую)

```yaml
push:
  if: |
    github.event_name == 'push' && (
      github.ref == 'refs/heads/main' ||
      github.ref == 'refs/heads/develop' ||
      startsWith(github.ref, 'refs/heads/release/')
    ) ||
    github.event_name == 'pull_request' &&
    contains(github.event.pull_request.labels.*.name, 'deploy-preview')
```

**Что пушится**:
- ✅ `main` - production
- ✅ `develop` - staging
- ✅ `release/*` - release candidates
- ✅ PR с label `deploy-preview` - для demo/testing

**Cleanup**:
- Manual: через GitHub UI → Packages → Delete version
- Automatic: GitHub Actions scheduled cleanup

### Вариант B: Conservative (текущая)

Оставить как есть - только `main` и `develop`.

**Для тестирования feature**:
```bash
# Локальная сборка и push
docker build -t ghcr.io/m2v0a02/gitops:feature-test ./app
docker push ghcr.io/m2v0a02/gitops:feature-test
```

---

## Image Retention Policies

### Политика хранения

```yaml
# .github/workflows/cleanup-images.yml
name: Cleanup Old Images

on:
  schedule:
    - cron: '0 0 * * 0'  # Каждое воскресенье

jobs:
  cleanup:
    runs-on: ubuntu-latest
    steps:
      - name: Delete untagged images
        run: |
          # Удалить образы без тегов

      - name: Delete old SHA-tagged images
        run: |
          # Оставить последние 10 по каждой ветке
          # Удалить старше 30 дней

      - name: Keep protected images
        run: |
          # НИКОГДА не удалять:
          # - latest
          # - main
          # - develop
          # - semver tags (v1.0.0)
```

### Размер хранилища

**GitHub Container Registry (Public)**:
- Storage: Unlimited (free)
- Bandwidth: 1GB/month included, потом $0.25/GB

**Рекомендации**:
- Хранить все production образы (с semver tags)
- Хранить последние N образов по ветке
- Удалять feature branch образы после merge

---

## Пример: Workflow для Feature Branch

### Текущая ситуация

```bash
# Developer работает над feature/awesome-api
git checkout -b feature/awesome-api
# пишет код...
git push origin feature/awesome-api
```

**CI запускается**:
```
✅ Lint
✅ Security
✅ Test
✅ Build Docker image (ghcr.io/m2v0a02/gitops:test)
✅ Test image (health check)
⏭️  Push (SKIPPED - не main/develop)
```

**Образ**: Существует только в CI runner, удаляется после job

### Если нужно протестировать feature в K8s

**Опция 1: Локальный build & push**
```bash
docker build -t ghcr.io/m2v0a02/gitops:feature-awesome-api ./app
docker push ghcr.io/m2v0a02/gitops:feature-awesome-api

# Обновить манифест
cd k8s/overlays/dev
yq eval '.images[0].newTag = "feature-awesome-api"' -i kustomization.yaml
kubectl apply -k .
```

**Опция 2: Временно изменить условие**
```yaml
# В PR можно попросить добавить:
if: github.ref == 'refs/heads/feature/awesome-api'
```

**Опция 3: PR label (best practice)**
```yaml
# Добавить label "deploy-preview" в PR
if: contains(github.event.pull_request.labels.*.name, 'deploy-preview')
```

---

## Cache Management

### Docker BuildKit Cache

```bash
# Посмотреть размер cache
gh api repos/M2V0A02/gitops/actions/cache/usage

# Очистить cache (manual)
gh api repos/M2V0A02/gitops/actions/caches -X DELETE
```

### Best Practices

1. **Layer ordering** - часто меняющееся в конец Dockerfile
2. **Multi-stage builds** - уменьшить финальный образ
3. **Cache dependencies** - pip, npm отдельными layers
4. **Cache invalidation** - при изменении requirements.txt

---

## Storage Cost Calculation

### Example: 100 feature branches/month

**Scenario 1: Push all features**
- 100 branches × 150MB = 15GB/month
- Storage: Free (public repo)
- Bandwidth: Depends on pulls
- **Cost**: $0

**Scenario 2: Only main/develop (current)**
- 2 branches × 150MB × 30 versions = 9GB
- Storage: Free
- **Cost**: $0

**Cleanup needed?**: При >50GB стоит задуматься о cleanup

---

## Monitoring

### Track image usage

```bash
# Посмотреть все образы
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://api.github.com/users/M2V0A02/packages/container/gitops/versions

# Посмотреть downloads
gh api /users/M2V0A02/packages/container/gitops/versions | \
  jq '.[] | {name: .name, downloads: .metadata.container.tags}'
```

---

## Recommendations для вашего проекта

### Сейчас (Learning Phase)

✅ **Оставить как есть** - только main/develop
- Простота
- Нет лишних образов
- Фокус на CI/CD и ArgoCD обучении

### Позже (Production)

✅ **Добавить**:
1. Semver tags (`v1.0.0`)
2. PR preview deployments (с label)
3. Scheduled cleanup
4. Image signing (cosign)

### Не рекомендую

❌ Push всех feature веток автоматически
❌ Хранить образы без retention policy
❌ Использовать `latest` для production

---

## Quick Reference

```bash
# Где хранятся образы?
https://github.com/M2V0A02/pkgs/container/gitops

# Какие ветки пушатся?
main, develop (в вашем случае)

# Feature ветки билдятся?
Да, но НЕ пушатся в registry

# Где образ feature ветки?
В GitHub Actions cache (7 дней)

# Как протестировать feature?
1. Merge в develop
2. Manual build & push
3. Add PR label "deploy-preview"

# Очистка старых образов?
Manual: GitHub UI → Delete version
Auto: Scheduled workflow (TODO)
```

---

## Summary

| Вопрос | Ответ |
|--------|-------|
| **CI всегда создает образ?** | ✅ Да, для ВСЕХ веток (build job) |
| **Всегда пушит в registry?** | ❌ Нет, только main/develop (push job) |
| **Feature образы где?** | В CI cache, удаляются после job |
| **Десятки feature веток?** | Не проблема - не пушатся в registry |
| **Как тестировать feature?** | Merge в develop или manual push |
| **Retention policy?** | Manual cleanup сейчас, auto - TODO |

**Текущая стратегия идеальна для обучения и небольших проектов!**
