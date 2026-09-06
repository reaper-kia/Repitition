# CONTRACTS.md — договорённости между модулями

Этот файл — единственная правда о том, что течёт между модулями и в какой
форме. Пока мы это обсуждаем — он живёт как markdown. Когда начинаем
писать код — каждый раздел почти буквально переезжает в
`src/modules/<module>/application/ports/*.py` своего модуля.

**Это не сетевой API.** У нас один процесс, один Python. Класс из этого
файла — это не JSON, который летит по HTTP, это Python-объект, который
один модуль напрямую передаёт другому внутри одного вызова. Поэтому здесь
нет версионирования, нет эндпоинтов, нет статус-кодов — только форма данных
и способ вызова.

**У каждой границы два свойства:**
- **Форма** — какие поля, какие типы. Это dataclass ниже.
- **Способ вызова** — `ПРЯМОЙ` (синхронный вызов функции, ждём ответ сразу)
  или `СОБЫТИЕ` (кладём в очередь, обработается позже, ответа не ждём).
  Прямой вызов — когда нужен результат сразу для решения (деньги).
  Событие — когда лаг в секунды не страшен (лидерборд, ачивки).

---

## 1. Identity/Auth → все модули

**Способ:** ПРЯМОЙ. Не межмодульный вызов, а FastAPI-зависимость, которую
подключает роут любого модуля.

**Где живёт:** `src/shared/domain/actor.py` (сам класс — общий, ничей),
производящая функция — `src/modules/auth/api/dependencies.py`.

```python
@dataclass(frozen=True)
class RequestActor:
    user_id: UUID
    role: Literal["CLIENT", "CLUB_MANAGER", "NETWORK_ADMIN"]
```

**Предусловие:** у `User` сейчас есть только `is_admin: bool`. Нужен enum
`role` на три значения — это первая правка, без неё `RequestActor` собрать
не из чего.

---

## 2. Club → Client, Visit, Rewards, Engagement

**Способ:** ПРЯМОЙ. Нужно знать *до* записи, активен ли клуб — это условие
для решения, не факт постфактум.

**Где живёт:** `src/modules/club/application/ports/club_queries.py` (со
стороны Club — реализация; со стороны вызывающих — просто зовут функцию).

```python
@dataclass(frozen=True)
class ClubScope:
    club_id: UUID
    is_active: bool
    manager_user_id: UUID
```

**Правило:** любой модуль, принимающий `club_id` в команде, обязан
проверить `is_active` до записи в свою таблицу.

---

## 3. Client → Visit, Engagement, Rewards

**Способ:** ПРЯМОЙ для снапшота (нужен при принятии решения),
СОБЫТИЕ для факта первой покупки (Rewards может обработать чуть позже).

**Где живёт:** снапшот — `src/modules/client/application/ports/client_queries.py`.
Событие — `src/modules/client/domain/events.py`, публикуется через Outbox.

```python
@dataclass(frozen=True)
class ClientSnapshot:
    client_id: UUID
    club_id: UUID
    status: Literal["ACTIVE", "EXPIRED", "BLOCKED"]
    referred_by_client_id: UUID | None
```

```python
@dataclass(frozen=True)
class FirstMembershipPurchased:
    client_id: UUID
    club_id: UUID
    referred_by_client_id: UUID | None
    purchase_id: UUID
    occurred_at: datetime
```

---

## 4. Visit → Engagement

**Способ:** СОБЫТИЕ. Прогресс челленджа, лидерборд и ачивки могут
отстать на секунду-две — это не денежная операция.

**Где живёт:** `src/modules/visit/domain/events.py` → Outbox → Engagement
подписан как consumer (или, для хакатона проще — Visit после сохранения
визита напрямую зовёт `engagement_event_handler.handle(VisitRecorded(...))`
в том же запросе, без Kafka. Это компромисс скорости разработки, не
идеал — если считаете, что реальный async важнее, скажите, вернёмся
к Outbox).

```python
@dataclass(frozen=True)
class VisitRecorded:
    visit_id: UUID
    client_id: UUID
    club_id: UUID
    entered_at: datetime
```

Один обработчик на это событие в Engagement двигает сразу три вещи —
не три разных подписки, один хендлер:

```
on VisitRecorded:
    1. ClientChallenge.advance(client_id)                         # было
    2. redis.zincrby(f"leaderboard:{club_id}:{week}", client_id, 1)  # новое
    3. AchievementRule.check(client_id, rule_type="VISITS_TOTAL")    # новое
    # Rank ничего не пишет — это чтение по требованию, а не реакция на событие
```

Идемпотентность по `visit_id` — забота Visit (у вас уже есть external id).
Если событие пришло дважды с одним `visit_id` — это баг Visit, Engagement
не обязан защищаться повторно.

---

## 5. Engagement → Rewards — денежная граница, самая важная

**Способ:** ПРЯМОЙ, всегда. Engagement обязан знать результат сразу,
чтобы решить, выдавать награду или нет.

**Где живёт:** со стороны Rewards — `src/modules/rewards/application/ports/reward_gateway.py`
(имя условное, определитесь с реальным). Engagement импортирует и зовёт
как обычную функцию/команду через Mediator, только Mediator здесь —
не свой, а Rewards-овский, точнее — Engagement напрямую вызывает
application-слой Rewards, минуя HTTP.

**Договорённость, которую нужно принять явно:** сумму в рублях считает
**Engagement** (у него веса этапов и конфиг), Rewards только проверяет
лимит и резервирует. Rewards не должен знать про существование процентов
50/30/20 — это продуктовая логика, а не финансовая.

**Шаг 1 — резерв, разово при старте программы/набора:**

```python
@dataclass(frozen=True)
class ReserveBudgetCommand:
    club_id: UUID
    source_type: Literal["CHALLENGE_COHORT", "REFERRAL", "RETENTION"]
    source_id: UUID
    amount: Decimal
    idempotency_key: str

@dataclass(frozen=True)
class BudgetReservationResult:
    reservation_id: UUID | None
    status: Literal["RESERVED", "INSUFFICIENT_FUNDS"]
```

**Шаг 2 — списание, по факту выполнения условия:**

```python
@dataclass(frozen=True)
class ConsumeReservationCommand:
    reservation_id: UUID
    amount: Decimal
    grant_purpose: Literal["ONBOARDING", "REFERRAL_INVITEE", "REFERRAL_REFERRER", "RETENTION"]
    client_id: UUID
    source_key: str

@dataclass(frozen=True)
class DiscountGrantResult:
    grant_id: UUID | None
    status: Literal["GRANTED", "ALREADY_GRANTED", "RESERVATION_EXHAUSTED"]
```

`ALREADY_GRANTED` — нормальный ответ, не ошибка. Engagement всегда шлёт
команду при выполнении условия; помнить «выдавали или нет» — не его
работа, это делает Rewards через `source_key UNIQUE`.

**Почему шаг 1 и 2 разнесены во времени, а не одна транзакция:** потому
что резерв и потребление могут случиться в разных запросах с разницей
в дни. Разделение на «резерв → потом трать» — это ровно то, что защищает
вас от необходимости заворачивать оба модуля в одну общую транзакцию.
Ваша собственная идея с `BudgetReservation` уже решает проблему
согласованности между модулями — я её не меняю, просто показываю, что
она делает не только «показываем суммы после резерва», но и снимает
головную боль с межмодульной атомарности.

**Achievement за Leaderboard — эта граница не существует вовсе**, если
приз неденежный: Engagement выдаёт `ClientAchievement` сам себе, Rewards
не участвует. Ровно поэтому я предлагал держать призы за топ недели
бесплатными — не из экономии, а чтобы не плодить ещё одну денежную
границу вдобавок к онбордингу и реферałу.

---

## 6. Rewards → Client — перед подтверждением покупки

**Способ:** ПРЯМОЙ.

```python
@dataclass(frozen=True)
class GetApplicableGrantsQuery:
    client_id: UUID
    purchase_type: Literal["MEMBERSHIP", "RENEWAL", "PERSONAL_TRAINING", "PRODUCT"]

@dataclass(frozen=True)
class ApplicableGrant:
    grant_id: UUID
    amount: Decimal
    purpose: str
```

Client получает список `ApplicableGrant`, сам решает сколько применить
в пределах cap. Погашение — в одной транзакции с созданием `Purchase`,
это уже верно описано в вашей исходной таблице, здесь не меняется.

---

## 7. Engagement → панель управляющего

Не межмодульная граница (это чтение для UI), но форма важна — от неё
зависит, что нарисует фронтендер.

```python
@dataclass(frozen=True)
class RetentionCaseSummary:
    case_id: UUID
    client_id: UUID
    client_name: str
    risk_score: float        # 0..1. Нет ML -> правило даёт 0.0 или 1.0
    risk_reasons: list[str]  # ["11 дней без визита", "пропали групповые"]
    detected_at: datetime
```

Сортировка — `risk_score DESC`. Пагинация с cap **20 записей на страницу**.

---

## Нерешённое — принять явно, до раздачи ТЗ

1. Кто считает сумму скидки в рублях — **предложение: Engagement**.
2. Призы за Leaderboard — деньги или ачивки — **предложение: ачивки**.
3. Кто вызывает ML-сервис для `risk_score` — Engagement синхронно при
   создании `RetentionCase`, или отдельный фоновый job раз в день.
4. `VisitRecorded`: прямой вызов внутри запроса (проще для хакатона) или
   через Outbox/Kafka (честный async, но больше кода и настройки).