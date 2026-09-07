from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.modules.engagement.domain.enums import (
    AchievementRuleType,
    ChallengeStatus,
    ClientChallengeStatus,
    RetentionCaseStatus,
    RetentionDecision,
)
from src.modules.engagement.domain.exceptions import (
    ChallengeAlreadyPublishedError,
    RetentionCaseAlreadyResolvedError,
    StageAlreadyCompletedError,
)
from src.modules.engagement.domain.value_objects import ChallengeStage, RiskSnapshot


@dataclass
class Challenge:
    """Программа адаптации новых клиентов на первые 60 дней.

    Неденежная: этапы выдают ачивки. Опубликованная версия неизменяема —
    правки создают следующую версию, чтобы у клиента не менялись условия
    на середине пути.
    """

    club_id: UUID | None  # None = программа всей сети
    version: int
    stages: list[ChallengeStage]
    status: ChallengeStatus = ChallengeStatus.DRAFT
    id: UUID = field(default_factory=uuid4)

    @classmethod
    def draft(
        cls, club_id: UUID | None, version: int, stages: list[ChallengeStage]
    ) -> "Challenge":
        ordered = sorted(stages, key=lambda stage: stage.order)
        return cls(club_id=club_id, version=version, stages=ordered)

    def publish(self) -> None:
        if self.status is not ChallengeStatus.DRAFT:
            raise ChallengeAlreadyPublishedError("Only a draft can be published")
        if not self.stages:
            raise ChallengeAlreadyPublishedError("Challenge must contain stages")
        self.status = ChallengeStatus.ACTIVE

    def stage_by_order(self, order: int) -> ChallengeStage | None:
        return next((stage for stage in self.stages if stage.order == order), None)

    @property
    def total_stages(self) -> int:
        return len(self.stages)


@dataclass
class ClientChallenge:
    """Участие конкретного клиента в программе.

    Фиксирует только выполнение условия. Денег не касается вовсе.
    """

    client_id: UUID
    challenge_id: UUID
    challenge_version: int
    total_stages: int
    current_stage: int = 1
    visits_in_stage: int = 0
    status: ClientChallengeStatus = ClientChallengeStatus.IN_PROGRESS
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    ends_at: datetime | None = None
    id: UUID = field(default_factory=uuid4)

    def register_visit(self, required_visits: int) -> bool:
        """Возвращает True, если этим визитом этап закрыт.

        Вызывается обработчиком VisitRecorded. Идемпотентность по visit_id
        обеспечивает Visit — сюда один визит приходит один раз.
        """
        if self.status is not ClientChallengeStatus.IN_PROGRESS:
            return False

        self.visits_in_stage += 1
        if self.visits_in_stage < required_visits:
            return False

        return True

    def complete_stage(self) -> None:
        if self.status is not ClientChallengeStatus.IN_PROGRESS:
            raise StageAlreadyCompletedError("Challenge is not in progress")

        if self.current_stage >= self.total_stages:
            self.status = ClientChallengeStatus.COMPLETED
        else:
            self.current_stage += 1
        self.visits_in_stage = 0

    def expire(self) -> None:
        if self.status is ClientChallengeStatus.IN_PROGRESS:
            self.status = ClientChallengeStatus.EXPIRED


@dataclass
class AchievementDefinition:
    """Каталог правил выдачи ачивок. Задаётся администратором сети.

    Денег не касается: RewardBudget здесь не участвует. Именно поэтому
    ачивки — самая дешёвая механика вовлечения из доступных.
    """

    code: str
    title: str
    icon: str
    rule_type: AchievementRuleType
    threshold: int
    id: UUID = field(default_factory=uuid4)

    def is_satisfied_by(self, measured_value: int) -> bool:
        return measured_value >= self.threshold


@dataclass
class ClientAchievement:
    """Факт выдачи ачивки клиенту.

    source_key UNIQUE — тот же паттерн идемпотентности, что у DiscountGrant
    в Rewards. Повторный пересчёт после того же визита не создаёт дубль.

    Примеры source_key:
        f"visits_total:{client_id}:{code}"
        f"leaderboard:{club_id}:{iso_week}:{client_id}"
        f"stage:{client_challenge_id}:{stage_order}"
    """

    client_id: UUID
    achievement_definition_id: UUID
    achievement_code: str
    source_key: str
    achieved_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: UUID = field(default_factory=uuid4)

    @classmethod
    def grant(
        cls,
        client_id: UUID,
        definition: AchievementDefinition,
        source_key: str,
    ) -> "ClientAchievement":
        return cls(
            client_id=client_id,
            achievement_definition_id=definition.id,
            achievement_code=definition.code,
            source_key=source_key,
        )


@dataclass
class RetentionCase:
    """Карточка риска оттока для панели управляющего.

    Ключевое продуктовое решение: простое отсутствие НЕ выдаёт скидку
    автоматически. Кейс — это объяснение и рекомендация, решение принимает
    человек. Иначе клиенты научились бы переставать ходить ради бонуса.

    risk_score и risk_reasons приходят из ML-сервиса. Если ML недоступен,
    правило даёт 0.0/1.0 и одну причину — карточки продолжают работать.

    Нужен UNIQUE на (client_id, status=OPEN), чтобы ежедневный job
    не плодил дубли.
    """

    client_id: UUID
    club_id: UUID
    risk_score: float
    risk_reasons: list[str]
    snapshot: RiskSnapshot
    status: RetentionCaseStatus = RetentionCaseStatus.OPEN
    decision: RetentionDecision | None = None
    decided_by_user_id: UUID | None = None
    manager_comment: str | None = None
    detected_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    decided_at: datetime | None = None
    id: UUID = field(default_factory=uuid4)

    @classmethod
    def detect(
        cls,
        client_id: UUID,
        club_id: UUID,
        risk_score: float,
        risk_reasons: list[str],
        snapshot: RiskSnapshot,
    ) -> "RetentionCase":
        return cls(
            client_id=client_id,
            club_id=club_id,
            risk_score=max(0.0, min(1.0, risk_score)),
            risk_reasons=risk_reasons,
            snapshot=snapshot,
        )

    def resolve(
        self,
        decision: RetentionDecision,
        decided_by_user_id: UUID,
        comment: str | None = None,
    ) -> None:
        """Решение управляющего. Статус OFFER_CREATED ставится НЕ здесь,
        а только после успешного резерва в Rewards — иначе мы пообещаем
        скидку, под которую нет денег."""
        if self.status is not RetentionCaseStatus.OPEN:
            raise RetentionCaseAlreadyResolvedError("Case is already resolved")

        self.decision = decision
        self.decided_by_user_id = decided_by_user_id
        self.manager_comment = comment
        self.decided_at = datetime.now(UTC)

        if decision is RetentionDecision.DISMISS:
            self.status = RetentionCaseStatus.DISMISSED

    def confirm_offer(self) -> None:
        """Вызывается только после того, как Rewards вернул GRANTED."""
        self.status = RetentionCaseStatus.OFFER_CREATED
