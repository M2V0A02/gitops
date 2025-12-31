# Создание GitHub репозитория

## Вариант 1: Через веб-интерфейс (Самый простой)

### Шаг 1: Создайте репозиторий на GitHub
1. Откройте https://github.com/new
2. Repository name: **gitops**
3. Description: **GitOps CI/CD testing project with ArgoCD, K3s, and GitHub Actions**
4. Выберите: **Public** (для бесплатного GHCR и публичных образов)
5. **НЕ** ставьте галочки на:
   - ❌ Add a README file
   - ❌ Add .gitignore
   - ❌ Choose a license
6. Нажмите **Create repository**

### Шаг 2: Запушьте код (я уже всё настроил!)
```bash
cd /home/tarakan/Documents/project/gitops

# Всё уже готово, просто запушьте:
git push -u origin main

# Создайте develop ветку
git push -u origin develop
```

---

## Вариант 2: Через GitHub CLI (если установлен)

```bash
# Установите gh CLI
sudo dnf install gh
# или
sudo snap install gh

# Залогиньтесь
gh auth login

# Создайте репозиторий
gh repo create gitops --public --source=. --remote=origin --push

# Запушьте develop
git push -u origin develop
```

---

## Вариант 3: Через API с Personal Access Token

### Создайте токен:
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token (classic)
3. Scopes: `repo` (все подпункты)
4. Generate token → скопируйте токен

### Создайте репозиторий:
```bash
# Замените YOUR_TOKEN на ваш токен
curl -X POST \
  -H "Authorization: token YOUR_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/user/repos \
  -d '{
    "name": "gitops",
    "description": "GitOps CI/CD testing project with ArgoCD, K3s, and GitHub Actions",
    "private": false
  }'

# Затем запушьте
cd /home/tarakan/Documents/project/gitops
git push -u origin main
git push -u origin develop
```

---

## ✅ Что уже сделано автоматически

- ✅ Git инициализирован
- ✅ Все файлы добавлены в коммит
- ✅ Username обновлен в ArgoCD манифестах (M2V0A02)
- ✅ Создан initial commit
- ✅ Ветка переименована в main
- ✅ Создана ветка develop
- ✅ Remote настроен: git@github.com:M2V0A02/gitops.git

## 🎯 Что нужно сделать

1. **Создать репозиторий на GitHub** (Вариант 1 - самый простой)
2. **Запушить код**:
   ```bash
   git push -u origin main
   git push -u origin develop
   ```

## 🚀 После создания репозитория

### Проверьте настройки GitHub Actions
1. Settings → Actions → General
2. Workflow permissions: **Read and write permissions** ✅
3. Allow GitHub Actions to create and approve pull requests ✅

### (Опционально) Настройте окружения
1. Settings → Environments
2. Создайте `staging` и `production`
3. Добавьте Required reviewers

### Проверьте первый запуск CI
```bash
# Создайте тестовый коммит
echo "# Test" >> README.md
git add README.md
git commit -m "Test CI pipeline"
git push origin develop

# Проверьте:
# GitHub → Actions → должен запуститься CI workflow
```

---

## 📊 Статус

```
✅ Локальный репозиторий готов
✅ Username обновлен (M2V0A02)
✅ SSH ключи работают
⏳ Создайте репозиторий на GitHub.com
⏳ Запушьте код
```

Всё готово для push!
