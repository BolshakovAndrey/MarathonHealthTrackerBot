# 🗺️ Deployment Map — MarathonHealthTrackerBot

Карта всех деплоев проекта. Два бота, две БД.

---

## 🌐 Схема окружений

```
GitHub: dev ──────────────────────────────────────────────────► STAGING
                health-bot-staging
                Railway staging env
                @MarathonHealthStagingBot
                health-bot-staging.up.railway.app


GitHub: main ──────────────────────────────────────────────────► PRODUCTION
                health-bot
                Railway production env
                @MarathonHealthBot
                health-bot-production.up.railway.app
```

---

## 📊 Быстрая таблица

| Компонент | Production | Staging |
|---|---|---|
| **Git ветка** | `main` | `dev` |
| **Бот** | @MarathonHealthBot | @MarathonHealthStagingBot |
| **API** | health-bot-production.up.railway.app | health-bot-staging.up.railway.app |
| **БД** | Railway Postgres | Railway Postgres-staging |
| **Railway env** | production | staging |

---

## 🚂 Railway — проект MarathonHealthTracker

**ID:** TBD (после создания)

### Сервисы production

| Сервис | Репозиторий | Назначение |
|---|---|---|
| `health-bot` | MarathonHealthTrackerBot | Telegram бот |
| `Postgres` | — | PostgreSQL production |

### Сервисы staging

| Сервис | Репозиторий | Назначение |
|---|---|---|
| `health-bot-staging` | MarathonHealthTrackerBot | Telegram бот |
| `Postgres-staging` | — | PostgreSQL staging |

---

## ⚙️ Переменные окружения

### Production (`health-bot`)
```bash
BOT_TOKEN=<prod_bot_token>
DATABASE_URL=${{Postgres.DATABASE_URL}}
APP_ENV=production
TIMEZONE=Europe/Belgrade
DAILY_DEADLINE=23:00
REMINDER_TIME=20:00
MIN_STEPS=8000
```

### Staging (`health-bot-staging`)
```bash
BOT_TOKEN=<staging_bot_token>
DATABASE_URL=${{Postgres-staging.DATABASE_URL}}
APP_ENV=staging
TIMEZONE=Europe/Belgrade
ENABLE_DEBUG=1
DAILY_DEADLINE=23:00
REMINDER_TIME=20:00
MIN_STEPS=8000
```

---

## 🤖 BotFather

| Бот | Token | Environment |
|---|---|---|
| @MarathonHealthBot | `<prod_token>` | Production |
| @MarathonHealthStagingBot | `<staging_token>` | Staging |

---

## 🔄 Git Workflow

### Feature Development
```bash
git checkout dev
git checkout -b feature/water-tracking
# ... code ...
git commit -m "feat: Water tracking handler"
git push -u origin feature/water-tracking
git checkout dev
git merge feature/water-tracking
git push  # → auto-deploy to staging
```

### Release to Production
```bash
git checkout main
git merge dev
git tag -a v0.1.0 -m "Sprint 1 complete"
git push --tags
git push  # → auto-deploy to production
git checkout dev
```

---

## 🧪 Чеклист перед деплоем

### Staging
- [ ] `DATABASE_URL` задан через `${{Postgres-staging.DATABASE_URL}}`
- [ ] `BOT_TOKEN` совпадает с @MarathonHealthStagingBot
- [ ] `ENABLE_DEBUG=1` задан
- [ ] Сервис перезапущен после изменения переменных
- [ ] Бот отвечает на `/start` в staging

### Production
- [ ] Все тесты прошли в staging
- [ ] `DATABASE_URL` задан через `${{Postgres.DATABASE_URL}}`
- [ ] `BOT_TOKEN` совпадает с @MarathonHealthBot
- [ ] `APP_ENV=production`
- [ ] Миграции БД выполнены
- [ ] Backup БД создан
- [ ] Бот отвечает на `/start` в production

---

## 🚨 Railway CLI

```bash
# Проверить текущее окружение
railway status

# Переключиться в staging
railway environment staging

# Переменные сервиса
railway variables --service health-bot-staging

# Задать переменную
railway variables --set "KEY=value"

# Логи
railway logs --service health-bot-staging

# Вернуться в production
railway environment production
```

---

## 🐛 Частые проблемы

| Симптом | Решение |
|---|---|
| Бот не отвечает | Проверить `BOT_TOKEN` в Railway variables |
| Database error | Проверить `DATABASE_URL=${{Postgres.DATABASE_URL}}` |
| "No module named..." | Добавить в `requirements.txt` → redeploy |
| Бот падает при старте | Проверить логи: `railway logs` |

---

## 📦 Future: Mini App

Если в будущем добавим Telegram Mini App:

### Netlify Setup
- **Репо:** MarathonHealthTrackerBot
- **Base dir:** `mini-app/`
- **Build:** `npm ci && npm run build`

| Контекст | URL | VITE_API_URL |
|---|---|---|
| Production (main) | `marathon-health.netlify.app` | `health-bot-production.up.railway.app` |
| Staging (dev) | `dev--marathon-health.netlify.app` | `health-bot-staging.up.railway.app` |

---

**Last Updated:** 20.02.2026  
**Maintainer:** PM Мак (@BolshakovClawBot)
