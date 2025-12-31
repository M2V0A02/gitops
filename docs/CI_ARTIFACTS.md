# CI/CD Pipeline Артефакты

## Что создает CI Pipeline?

### 1. 📦 Docker Image (Главный артефакт)

**Registry**: GitHub Container Registry (GHCR)
**URL**: https://github.com/M2V0A02/gitops/pkgs/container/gitops

#### Доступные образы:

```bash
# Latest версия (main branch)
ghcr.io/m2v0a02/gitops:latest

# По ветке
ghcr.io/m2v0a02/gitops:main
ghcr.io/m2v0a02/gitops:develop

# По коммиту (immutable)
ghcr.io/m2v0a02/gitops:main-dc927a4
ghcr.io/m2v0a02/gitops:develop-b2aeb07
```

#### Стратегия тегирования (из .github/workflows/ci.yaml)

```yaml
tags: |
  type=ref,event=branch              # main, develop
  type=sha,prefix={{branch}}-        # main-abc123, develop-xyz789
  type=semver,pattern={{version}}    # v1.0.0 (если есть git tag)
  type=raw,value=latest,enable=${{ github.ref == 'refs/heads/main' }}
```

**Результат**:
- `main` ветка → `latest`, `main`, `main-{sha}`
- `develop` ветка → `develop`, `develop-{sha}`
- Git tag `v1.0.0` → `1.0.0`, `1.0`, `1`

#### Использование образа

```bash
# Скачать
docker pull ghcr.io/m2v0a02/gitops:latest

# Запустить локально
docker run -p 5000:5000 ghcr.io/m2v0a02/gitops:latest

# Проверить
curl http://localhost:5000/health
```

#### Содержимое образа

- **Base**: `python:3.11-slim` (multi-stage build)
- **App**: Flask REST API
- **Size**: ~150-200 MB (оптимизирован)
- **User**: Non-root (appuser)
- **Port**: 5000
- **Healthcheck**: Built-in

---

### 2. 📝 Обновленные Kubernetes Манифесты

#### Какие файлы изменяются?

**Для develop ветки**:
```
k8s/overlays/dev/kustomization.yaml
```

**Для main ветки**:
```
k8s/overlays/staging/kustomization.yaml
```

#### Что именно обновляется?

```yaml
# До:
images:
  - name: gitops-demo-app
    newName: gitops-demo-app
    newTag: latest

# После CI:
images:
  - name: gitops-demo-app
    newName: ghcr.io/m2v0a02/gitops
    newTag: develop-dc927a4  # ← автоматически обновляется
```

#### Коммит от github-actions[bot]

```
Update image tag to develop-dc927a4

🤖 Generated with GitHub Actions

Co-Authored-By: M2V0A02 <M2V0A02@users.noreply.github.com>
```

---

### 3. 📊 Отчеты и Результаты

#### Test Coverage (Codecov)

- **Location**: GitHub Actions → Artifacts
- **Format**: XML + HTML
- **Coverage**: >70% (minimum threshold)
- **Uploaded to**: Codecov.io (if configured)

#### Security Scans

**Trivy (Container Scanning)**:
- **Location**: GitHub → Security → Code scanning alerts
- **Format**: SARIF
- **Severity**: CRITICAL, HIGH
- **Status**: Non-blocking (continue-on-error: true)

**Bandit (Python Security)**:
- **Location**: CI logs
- **Format**: JSON + Screen
- **Skipped**: B101 (assert), B104 (bind 0.0.0.0)

**Gitleaks (Secrets Detection)**:
- **Location**: CI logs
- **Format**: SARIF
- **Status**: Non-blocking

**Safety (Dependency Vulnerabilities)**:
- **Location**: CI logs
- **Status**: Non-blocking

#### Code Quality

- **flake8**: Linting (PEP8)
- **pylint**: Static analysis (score ≥ 8.0)
- **black**: Code formatting check

---

## Где найти артефакты?

### Docker Images

1. **GitHub UI**:
   - Repository → Packages → gitops
   - https://github.com/M2V0A02/gitops/pkgs/container/gitops

2. **CLI**:
   ```bash
   # Список тегов
   curl https://ghcr.io/v2/m2v0a02/gitops/tags/list

   # Pull образ
   docker pull ghcr.io/m2v0a02/gitops:latest
   ```

### Kubernetes Манифесты

1. **GitHub**:
   - Repository → Code → k8s/overlays/
   - Commits от github-actions[bot]

2. **Git**:
   ```bash
   git log --all --oneline --author="github-actions"
   ```

### CI Logs и Отчеты

1. **GitHub Actions**:
   - Repository → Actions → Latest run
   - https://github.com/M2V0A02/gitops/actions

2. **Security Tab**:
   - Repository → Security → Code scanning
   - Trivy results появляются здесь

---

## Жизненный цикл артефакта

### От кода до production

```
┌─────────────────┐
│ Developer       │
│ git push        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ GitHub Actions  │
│ CI Pipeline     │
├─────────────────┤
│ 1. Lint         │
│ 2. Test         │
│ 3. Build        │──┐
│ 4. Scan         │  │
│ 5. Push ────────┼──┼─► ghcr.io/m2v0a02/gitops:develop-abc123
│ 6. Update K8s   │  │
└────────┬────────┘  │
         │           │
         ▼           │
┌─────────────────┐  │
│ Git Repository  │  │
│ Updated:        │  │
│ kustomization   │  │
└────────┬────────┘  │
         │           │
         ▼           │
┌─────────────────┐  │
│ ArgoCD          │  │
│ Detects change  │  │
└────────┬────────┘  │
         │           │
         ▼           │
┌─────────────────┐  │
│ ArgoCD pulls ───┼──┘
│ from GHCR       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Kubernetes      │
│ Pods running    │
│ new version     │
└─────────────────┘
```

---

## Практическое использование

### Сценарий 1: Локальное тестирование артефакта

```bash
# 1. Скачать образ из CI
docker pull ghcr.io/m2v0a02/gitops:develop-abc123

# 2. Запустить локально
docker run -p 5000:5000 ghcr.io/m2v0a02/gitops:develop-abc123

# 3. Протестировать
curl http://localhost:5000/health
curl http://localhost:5000/api/items
```

### Сценарий 2: Ручной деплой в Kubernetes

```bash
# 1. Узнать последний тег
TAG=$(curl -s https://ghcr.io/v2/m2v0a02/gitops/tags/list | jq -r '.tags[0]')

# 2. Обновить манифест
cd k8s/overlays/staging
yq eval ".images[0].newTag = \"$TAG\"" -i kustomization.yaml

# 3. Применить
kubectl apply -k .
```

### Сценарий 3: Rollback к предыдущей версии

```bash
# 1. Посмотреть историю образов
# GitHub → Packages → gitops → Version history

# 2. Откатить манифест
git log k8s/overlays/dev/kustomization.yaml
git checkout HEAD~1 k8s/overlays/dev/kustomization.yaml

# 3. Коммит
git commit -m "Rollback to previous version"
git push

# ArgoCD автоматически применит откат
```

---

## Retention Policy

### Docker Images

**GitHub Container Registry**:
- Public образы: Unlimited storage
- Retention: Manual deletion required
- Cost: Free for public repositories

**Рекомендации**:
- Хранить все tagged versions (семантическое версионирование)
- Удалять временные SHA-tagged образы (старше 30 дней)
- Оставлять последние 10 develop образов

### Kubernetes Манифесты

**Git History**:
- Хранится навсегда в Git
- Можно откатиться к любой версии
- Полная audit trail

---

## Метаданные артефактов

### В Docker образе

```bash
docker inspect ghcr.io/m2v0a02/gitops:latest

# Labels:
org.opencontainers.image.source=https://github.com/M2V0A02/gitops
org.opencontainers.image.revision=dc927a4...
org.opencontainers.image.created=2025-12-31T11:20:00Z
```

### В Kubernetes манифесте

```yaml
metadata:
  labels:
    app.kubernetes.io/version: "develop-dc927a4"
    app.kubernetes.io/managed-by: argocd
```

---

## Troubleshooting

### Образ не скачивается

```bash
# Проверить доступность
docker pull ghcr.io/m2v0a02/gitops:latest

# Если ошибка "unauthorized":
# Для публичного образа авторизация не нужна
# Если образ private - нужен GitHub token
```

### Неправильный тег в манифесте

```bash
# Проверить последний коммит от github-actions
git log --author="github-actions" --oneline -1

# Посмотреть что изменилось
git show HEAD:k8s/overlays/dev/kustomization.yaml
```

### ArgoCD не видит новый образ

```bash
# 1. Проверить что манифест обновлен
git pull
cat k8s/overlays/dev/kustomization.yaml

# 2. Проверить что образ существует
docker pull ghcr.io/m2v0a02/gitops:develop-abc123

# 3. Force sync в ArgoCD
argocd app sync gitops-demo-dev --force
```

---

## Summary

✅ **Главный артефакт**: Docker образ в GHCR
✅ **Вспомогательные**: Обновленные K8s манифесты
✅ **Отчеты**: Coverage, Security scans, Linting
✅ **Доступность**: Публичные, можно скачать без авторизации
✅ **Immutable**: SHA-tagged образы никогда не меняются
✅ **GitOps ready**: Манифесты автоматически коммитятся в Git
