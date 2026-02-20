# 🏥 Health Tracker Bot - Project Plan

**PM:** Мак (OpenClaw Bot)  
**Developer:** Андрей Болшаков  
**Client:** Юля (нутрициолог)  
**Start Date:** 20.02.2026  
**Target Launch:** TBD

---

## 📋 PROJECT OVERVIEW

### Цель проекта
Создать Telegram бота для трекинга здоровья нутрициолога с функциями:
- 🧮 КБЖУ калькулятор (Миффлин-Сан Жеора)
- 💧 Трекинг воды
- 😊 Настроение (emoji picker)
- 😴 Сон (опционально, если есть трекер)
- 🤕 Мигрень/головные боли
- 📊 Статистика и аналитика

### Референсные проекты
- **MarathonBot** - классический aiogram бот с FSM
- **MarathonMiniApp** - FastAPI + React Mini App

### Tech Stack
- **Backend:** Python 3.12, aiogram 3, aiosqlite
- **Database:** SQLite (локально), PostgreSQL (production)
- **Scheduler:** APScheduler
- **Deploy:** Railway / VPS

---

## 🎯 MILESTONES

| # | Milestone | Target | Status | Progress |
|---|-----------|--------|--------|----------|
| M1 | Project Setup | Day 1 | 🟡 Planning | 0% |
| M2 | Core Infrastructure | Day 2-3 | ⚪ Pending | 0% |
| M3 | Profile & KBJU Calculator | Day 4-5 | ⚪ Pending | 0% |
| M4 | Daily Tracking Features | Day 6-8 | ⚪ Pending | 0% |
| M5 | Statistics & Reports | Day 9-10 | ⚪ Pending | 0% |
| M6 | Testing & Polish | Day 11-12 | ⚪ Pending | 0% |
| M7 | Deployment | Day 13 | ⚪ Pending | 0% |

**Total Estimated Time:** 13 days (при 3-4 часа/день разработки)

---

## 📦 WORK BREAKDOWN STRUCTURE (WBS)

### **PHASE 0: Project Initialization** ⚙️
**Goal:** Подготовка окружения и базовой структуры

#### Task 0.1: Repository Setup
- [ ] Создать директорию `~/.openclaw/workspace/health_tracker_bot/`
- [ ] Инициализировать git репозиторий
- [ ] Создать `.gitignore`
- [ ] Создать `README.md` с описанием проекта
- **Dependencies:** None
- **Estimate:** 30 min
- **Priority:** P0 (Critical)

#### Task 0.2: Project Structure
- [ ] Создать структуру папок (db/, handlers/, keyboards/, services/, states/, utils/)
- [ ] Создать пустые `__init__.py` файлы
- [ ] Создать `requirements.txt` (копировать из MarathonBot)
- [ ] Создать `.env.example` с шаблоном переменных
- **Dependencies:** 0.1
- **Estimate:** 20 min
- **Priority:** P0

#### Task 0.3: Environment Configuration
- [ ] Создать `.env` файл
- [ ] Получить BOT_TOKEN от @BotFather
- [ ] Настроить переменные окружения
- [ ] Создать `config.py` для загрузки конфига
- **Dependencies:** 0.2
- **Estimate:** 30 min
- **Priority:** P0

**Phase 0 Total Time:** 1.5 hours  
**Blocker Risk:** 🟢 Low

---

### **PHASE 1: Core Infrastructure** 🏗️
**Goal:** База данных, бот runner, базовые компоненты

#### Task 1.1: Database Schema
- [ ] Создать `db/database.py` (база из MarathonBot)
- [ ] Таблица `users` (user_id, username, full_name, gender, age, height, weight, activity_level, goal)
- [ ] Таблица `daily_targets` (bmr, tdee, calories, protein, fat, carbs)
- [ ] Таблица `water_log` (timestamp, amount_ml)
- [ ] Таблица `mood_log` (timestamp, emoji, note)
- [ ] Таблица `sleep_log` (date, hours, quality)
- [ ] Таблица `headache_log` (timestamp, intensity, location, triggers, duration)
- [ ] Миграции для добавления колонок
- **Dependencies:** 0.3
- **Estimate:** 2 hours
- **Priority:** P0

#### Task 1.2: Bot Loader
- [ ] Создать `loader.py` (инициализация bot, dispatcher, db)
- [ ] Настроить logging
- [ ] Подключение к базе данных
- **Dependencies:** 1.1
- **Estimate:** 30 min
- **Priority:** P0

#### Task 1.3: Entry Point
- [ ] Создать `app.py` (главная точка входа)
- [ ] Регистрация handlers
- [ ] Запуск polling
- [ ] Graceful shutdown
- **Dependencies:** 1.2
- **Estimate:** 30 min
- **Priority:** P0

#### Task 1.4: Basic Keyboards
- [ ] Создать `keyboards/inline_keyboards.py`
- [ ] Main menu keyboard
- [ ] Yes/No confirmation keyboard
- [ ] Cancel keyboard
- **Dependencies:** 1.3
- **Estimate:** 30 min
- **Priority:** P1

**Phase 1 Total Time:** 3.5 hours  
**Blocker Risk:** 🟢 Low

---

### **PHASE 2: User Profile & KBJU Calculator** 🧮
**Goal:** Онбординг, сбор данных, расчет метаболизма

#### Task 2.1: /start Handler
- [ ] Создать `handlers/start.py`
- [ ] Приветствие + описание бота
- [ ] Кнопка "Начать настройку профиля"
- [ ] Проверка существующего профиля
- **Dependencies:** 1.4
- **Estimate:** 1 hour
- **Priority:** P0

#### Task 2.2: Profile Setup FSM
- [ ] Создать `states/forms.py` (ProfileSetup states)
- [ ] Состояния: Gender → Age → Height → Weight → ActivityLevel → Goal
- [ ] Валидация ввода (age 10-100, height 100-250, weight 30-300)
- [ ] Сохранение в БД
- **Dependencies:** 2.1
- **Estimate:** 2 hours
- **Priority:** P0

#### Task 2.3: KBJU Calculator Service
- [ ] Создать `services/calculator.py`
- [ ] Функция `calculate_bmr()` - Миффлин-Сан Жеора
- [ ] Функция `calculate_tdee()` - BMR × коэффициент активности
- [ ] Функция `calculate_bju()` - распределение БЖУ по целям
- [ ] Коэффициенты цели (похудение -20%, поддержка 0%, набор +15%)
- **Dependencies:** None (utility)
- **Estimate:** 1.5 hours
- **Priority:** P0

#### Task 2.4: Display KBJU Results
- [ ] Создать красивое форматирование результатов
- [ ] Показать BMR, TDEE, итоговые калории
- [ ] Показать БЖУ в граммах
- [ ] Кнопки: "Сохранить" / "Пересчитать"
- **Dependencies:** 2.2, 2.3
- **Estimate:** 1 hour
- **Priority:** P1

#### Task 2.5: /profile Command
- [ ] Команда для просмотра профиля
- [ ] Показать все данные + текущие КБЖУ
- [ ] Кнопка "Изменить профиль"
- **Dependencies:** 2.4
- **Estimate:** 30 min
- **Priority:** P1

**Phase 2 Total Time:** 6 hours  
**Blocker Risk:** 🟡 Medium (зависит от валидации формул)

---

### **PHASE 3: Water Tracking** 💧
**Goal:** Трекинг потребления воды

#### Task 3.1: Water Handler
- [ ] Создать `handlers/water.py`
- [ ] Команда `/water` - показать статус за день
- [ ] Inline кнопки: +250мл | +500мл | +1л
- [ ] Кнопка "Другое количество" (FSM для ввода)
- **Dependencies:** 1.4
- **Estimate:** 1 hour
- **Priority:** P1

#### Task 3.2: Water Goal Setting
- [ ] Команда `/water_goal` - установить цель (литры/день)
- [ ] По умолчанию: 2.5л для женщин, 3.5л для мужчин
- [ ] Формула: вес_кг × 30мл
- [ ] Сохранение в профиле пользователя
- **Dependencies:** 3.1
- **Estimate:** 30 min
- **Priority:** P2

#### Task 3.3: Water Statistics
- [ ] Прогресс-бар за сегодня (🟦🟦🟦⬜⬜⬜⬜⬜ 60%)
- [ ] История за неделю (график emoji)
- [ ] Средний показатель за 7 дней
- **Dependencies:** 3.2
- **Estimate:** 1 hour
- **Priority:** P2

**Phase 3 Total Time:** 2.5 hours  
**Blocker Risk:** 🟢 Low

---

### **PHASE 4: Mood Tracking** 😊
**Goal:** Отслеживание настроения

#### Task 4.1: Mood Handler
- [ ] Создать `handlers/mood.py`
- [ ] Команда `/mood` - записать настроение
- [ ] Inline кнопки с emoji: 😄😊🙂😐😔😢😡😴
- [ ] Опционально: текстовая заметка
- **Dependencies:** 1.4
- **Estimate:** 45 min
- **Priority:** P1

#### Task 4.2: Mood History
- [ ] Показать последние 7 дней (emoji + дата)
- [ ] Определение тренда (улучшается/ухудшается)
- [ ] Статистика: сколько раз какой emoji
- **Dependencies:** 4.1
- **Estimate:** 1 hour
- **Priority:** P2

**Phase 4 Total Time:** 1.75 hours  
**Blocker Risk:** 🟢 Low

---

### **PHASE 5: Sleep Tracking** 😴
**Goal:** Опциональный трекинг сна

#### Task 5.1: Sleep Handler
- [ ] Создать `handlers/sleep.py`
- [ ] Команда `/sleep` - записать часы сна
- [ ] Inline кнопки: 4ч | 5ч | 6ч | 7ч | 8ч | 9ч | 10ч | Другое
- [ ] Опционально: качество (отлично/хорошо/плохо)
- **Dependencies:** 1.4
- **Estimate:** 1 hour
- **Priority:** P2 (опционально)

#### Task 5.2: Sleep Statistics
- [ ] Средние часы сна за неделю
- [ ] Рекомендация (норма 7-9 часов)
- [ ] График за 7 дней
- **Dependencies:** 5.1
- **Estimate:** 45 min
- **Priority:** P2

**Phase 5 Total Time:** 1.75 hours  
**Blocker Risk:** 🟢 Low (опциональная фича)

---

### **PHASE 6: Headache/Migraine Tracking** 🤕
**Goal:** Детальный трекинг головных болей

#### Task 6.1: Headache Handler
- [ ] Создать `handlers/headache.py`
- [ ] Команда `/headache` - записать эпизод
- [ ] FSM: Intensity (1-10) → Location → Triggers → Duration
- **Dependencies:** 1.4
- **Estimate:** 1.5 hours
- **Priority:** P1

#### Task 6.2: Headache Parameters
- [ ] Location: inline кнопки (вся голова/виски/лоб/затылок/односторонняя)
- [ ] Triggers: мульти-выбор (стресс/недосып/еда/погода/экраны/другое)
- [ ] Duration: inline кнопки (15мин/30мин/1ч/2ч/4ч/8ч+/Другое)
- **Dependencies:** 6.1
- **Estimate:** 1 hour
- **Priority:** P1

#### Task 6.3: Headache Analytics
- [ ] Частота эпизодов (за неделю/месяц)
- [ ] Самые частые триггеры
- [ ] Средняя интенсивность
- [ ] Паттерны (время суток, день недели)
- **Dependencies:** 6.2
- **Estimate:** 1.5 hours
- **Priority:** P2

**Phase 6 Total Time:** 4 hours  
**Blocker Risk:** 🟡 Medium (требует UX проработки)

---

### **PHASE 7: Statistics & Reports** 📊
**Goal:** Сводки и аналитика

#### Task 7.1: Daily Summary
- [ ] Создать `handlers/stats.py`
- [ ] Команда `/today` - сводка за сегодня
- [ ] Показать: вода (прогресс), настроение, сон, КБЖУ цели
- [ ] Эмодзи-индикаторы выполнения
- **Dependencies:** Phase 3, 4, 5
- **Estimate:** 1 hour
- **Priority:** P1

#### Task 7.2: Weekly Report
- [ ] Команда `/week` - отчет за неделю
- [ ] Графики: вода по дням, настроение тренд, сон
- [ ] Статистика: средние показатели
- [ ] Достижения и рекомендации
- **Dependencies:** 7.1
- **Estimate:** 2 hours
- **Priority:** P2

#### Task 7.3: Export Data
- [ ] Команда `/export` - выгрузка данных
- [ ] Формат CSV (для Excel/Google Sheets)
- [ ] Все логи за выбранный период
- **Dependencies:** 7.2
- **Estimate:** 1 hour
- **Priority:** P3 (nice to have)

**Phase 7 Total Time:** 4 hours  
**Blocker Risk:** 🟢 Low

---

### **PHASE 8: Scheduler & Reminders** ⏰
**Goal:** Автоматические напоминания

#### Task 8.1: APScheduler Setup
- [ ] Создать `services/scheduler.py`
- [ ] Настроить timezone (Europe/Belgrade)
- [ ] Интеграция с app.py
- **Dependencies:** 1.3
- **Estimate:** 30 min
- **Priority:** P1

#### Task 8.2: Daily Water Reminder
- [ ] Напоминание каждые 2 часа (10:00-20:00)
- [ ] Проверка: если выпито < 50% цели после 14:00 → напомнить
- [ ] Персонализация текста
- **Dependencies:** 8.1, Phase 3
- **Estimate:** 1 hour
- **Priority:** P1

#### Task 8.3: Evening Check-in
- [ ] Напоминание в 21:00 "Как прошёл день?"
- [ ] Если не записаны: настроение/вода/сон → предложить заполнить
- [ ] Кнопки быстрого доступа
- **Dependencies:** 8.1
- **Estimate:** 1 hour
- **Priority:** P2

**Phase 8 Total Time:** 2.5 hours  
**Blocker Risk:** 🟢 Low

---

### **PHASE 9: Testing & Polish** 🧪
**Goal:** Тестирование и улучшение UX

#### Task 9.1: Manual Testing
- [ ] Полный флоу: регистрация → настройка → все фичи
- [ ] Тестирование edge cases (невалидный ввод, пустые данные)
- [ ] Проверка всех кнопок и команд
- **Dependencies:** All phases
- **Estimate:** 2 hours
- **Priority:** P0

#### Task 9.2: Error Handling
- [ ] Обработка ошибок БД (try/except)
- [ ] Fallback сообщения для пользователя
- [ ] Логирование критических ошибок
- **Dependencies:** 9.1
- **Estimate:** 1 hour
- **Priority:** P0

#### Task 9.3: UX Improvements
- [ ] Улучшить тексты сообщений
- [ ] Добавить emoji и форматирование
- [ ] Оптимизировать navigation (меню кнопки)
- [ ] Помощь (/help команда)
- **Dependencies:** 9.1
- **Estimate:** 1.5 hours
- **Priority:** P1

#### Task 9.4: Performance Testing
- [ ] Проверка скорости ответов бота
- [ ] Оптимизация SQL запросов
- [ ] Нагрузочное тестирование (10+ пользователей)
- **Dependencies:** 9.2
- **Estimate:** 1 hour
- **Priority:** P2

**Phase 9 Total Time:** 5.5 hours  
**Blocker Risk:** 🟡 Medium (могут найтись баги)

---

### **PHASE 10: Deployment** 🚀
**Goal:** Запуск в продакшн

#### Task 10.1: Production Environment
- [ ] Настроить Railway / VPS
- [ ] Настроить PostgreSQL (или оставить SQLite)
- [ ] Настроить переменные окружения
- [ ] Настроить SSL (если нужен webhook)
- **Dependencies:** Phase 9
- **Estimate:** 1 hour
- **Priority:** P0

#### Task 10.2: Deploy
- [ ] Push код в git репозиторий
- [ ] Deploy на Railway
- [ ] Запустить бота
- [ ] Проверка работоспособности
- **Dependencies:** 10.1
- **Estimate:** 30 min
- **Priority:** P0

#### Task 10.3: Monitoring Setup
- [ ] Логирование в файл / Sentry
- [ ] Healthcheck endpoint (если webhook)
- [ ] Алерты при падении бота
- **Dependencies:** 10.2
- **Estimate:** 30 min
- **Priority:** P1

#### Task 10.4: Documentation
- [ ] Обновить README.md
- [ ] Инструкция для пользователя (Юля)
- [ ] Инструкция по деплою
- [ ] Changelog
- **Dependencies:** 10.3
- **Estimate:** 1 hour
- **Priority:** P1

**Phase 10 Total Time:** 3 hours  
**Blocker Risk:** 🟡 Medium (могут быть проблемы с инфраструктурой)

---

## 📊 PROJECT METRICS

### Development Efficiency Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| **Tasks Completed** | 47 | 0 | ⚪ |
| **Phases Completed** | 10 | 0 | ⚪ |
| **Total Time Spent** | 0h | 0h | ⚪ |
| **Estimated vs Actual Time** | ±20% | N/A | ⚪ |
| **Bugs Found** | 0 | 0 | 🟢 |
| **Bugs Fixed** | 0 | 0 | 🟢 |
| **Code Review Issues** | 0 | 0 | 🟢 |
| **Test Coverage** | N/A | N/A | ⚪ |

### Velocity Tracking

| Week | Planned Tasks | Completed Tasks | Completion Rate | Notes |
|------|---------------|-----------------|-----------------|-------|
| Week 1 | TBD | 0 | 0% | Planning phase |
| Week 2 | TBD | 0 | 0% | - |

### Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Неправильные формулы КБЖУ | 🟡 Medium | 🔴 High | Проверка через референсные калькуляторы |
| Сложность FSM логики | 🟡 Medium | 🟡 Medium | Использовать паттерны из MarathonBot |
| Проблемы с деплоем | 🟢 Low | 🟡 Medium | Тестирование на локальном окружении |
| Отсутствие требований от Юли | 🟡 Medium | 🔴 High | Ранний прототип для обратной связи |

---

## 🎯 SPRINT PLANNING

### Sprint 1 (Days 1-3): Foundation
**Goal:** Базовая инфраструктура и профили

**Tasks:**
- [ ] Phase 0: Project Setup (1.5h)
- [ ] Phase 1: Core Infrastructure (3.5h)
- [ ] Phase 2: Profile & KBJU (6h)

**Total:** 11 hours  
**Days:** 3 days @ 3-4h/day

### Sprint 2 (Days 4-7): Core Features
**Goal:** Все tracking фичи

**Tasks:**
- [ ] Phase 3: Water Tracking (2.5h)
- [ ] Phase 4: Mood Tracking (1.75h)
- [ ] Phase 5: Sleep Tracking (1.75h)
- [ ] Phase 6: Headache Tracking (4h)

**Total:** 10 hours  
**Days:** 3-4 days @ 3h/day

### Sprint 3 (Days 8-10): Analytics & Automation
**Goal:** Статистика и напоминания

**Tasks:**
- [ ] Phase 7: Statistics (4h)
- [ ] Phase 8: Scheduler (2.5h)

**Total:** 6.5 hours  
**Days:** 2-3 days @ 3h/day

### Sprint 4 (Days 11-13): Polish & Launch
**Goal:** Тестирование и деплой

**Tasks:**
- [ ] Phase 9: Testing (5.5h)
- [ ] Phase 10: Deployment (3h)

**Total:** 8.5 hours  
**Days:** 2-3 days @ 3-4h/day

---

## 📈 DAILY STANDUP FORMAT

### What I did yesterday:
- Task X.Y: [status]
- Blockers: [any issues]

### What I'm doing today:
- Task X.Y: [plan]

### Blockers/Questions:
- [any blockers or questions for PM]

---

## 🔄 PROGRESS TRACKING

### How to Update Progress:

```bash
# После завершения задачи:
1. Отметить [x] в чекбоксе задачи
2. Обновить Metrics: Tasks Completed +1
3. Записать фактическое время в Daily Log
4. Обновить статус Phase (если закончена)
5. Commit изменения
```

### Daily Log Format:

```
## Day X - DD.MM.YYYY

**Time Spent:** Xh Xmin  
**Tasks Completed:**
- [x] Task X.Y - Actual time: Xh

**Blockers:**
- None / [описание]

**Notes:**
- [любые заметки, находки, идеи]

**Tomorrow:**
- [ ] Task X.Y
```

---

## 🚦 STATUS INDICATORS

- 🟢 **On Track** - все идёт по плану
- 🟡 **At Risk** - есть задержки, но можем наверстать
- 🔴 **Blocked** - критический блокер, нужна помощь
- ⚪ **Not Started** - задача ещё не начата
- ✅ **Completed** - задача завершена

---

## 📞 PM AVAILABILITY

**Мак (PM Bot)** доступен 24/7 для:
- ❓ Вопросы по задачам
- 🔄 Обновление статуса
- 🐛 Обсуждение багов
- 💡 Идеи и улучшения
- 📊 Метрики прогресса

**Как связаться:**
- `@BolshakovClawBot` в General треде
- Упомянуть `@BolshakovClawBot` в любом сообщении

---

## 🎉 SUCCESS CRITERIA

Проект считается успешным если:
1. ✅ Все P0 и P1 задачи завершены
2. ✅ Юля может использовать бота ежедневно
3. ✅ КБЖУ калькулятор работает корректно (проверено вручную)
4. ✅ Все tracking фичи функциональны
5. ✅ Бот деплоен и стабильно работает
6. ✅ Completion rate ≥ 85% от плана

---

**Ready to start!** 🚀

**Next Step:** Андрей, когда готов начинать — пиши мне и я начну трекинг! Просто скажи "Начинаем Sprint 1" и я создам Daily Log.
