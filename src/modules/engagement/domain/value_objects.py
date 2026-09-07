from dataclasses import dataclass

from src.modules.engagement.domain.exceptions import ChallengeNotFoundError


@dataclass(frozen=True)
class ChallengeStage:
    """Один этап программы онбординга.

    ДЕНЕГ ЗДЕСЬ НЕТ. Онбординг неденежный: награда за этап — ачивка,
    а не скидка. Благодаря этому Challenge вообще не обращается к Rewards,
    и вся история с предварительным резервом фонда под месячный набор
    из проекта исчезает.

    order — порядковый номер, 1..N. Этапы проходятся последовательно.
    """

    order: int
    title: str
    duration_days: int
    required_visits: int
    reward_achievement_code: str

    def __post_init__(self) -> None:
        if self.order < 1:
            raise ChallengeNotFoundError("Stage order starts at 1")
        if self.duration_days < 1 or self.required_visits < 1:
            raise ChallengeNotFoundError(
                "Stage must require at least 1 day and 1 visit"
            )


@dataclass(frozen=True)
class RankTier:
    """Порог ранга. Конфиг, задаваемый администратором сети.

    Сам ранг клиента НЕ хранится: это наивысший тир, чей min_visits пройден,
    вычисляется на чтении из числа визитов и кэшируется в Redis.
    Ровно та же логика, по которой вы не храните visits_count.
    """

    code: str
    title: str
    min_visits: int

    def is_reached_by(self, visits_total: int) -> bool:
        return visits_total >= self.min_visits


@dataclass(frozen=True)
class RiskSnapshot:
    """Показатели на момент обнаружения риска. Замораживаются в RetentionCase,
    чтобы управляющий видел причину решения даже спустя неделю."""

    days_since_last_visit: int
    visits_last_30d: int
    visits_prev_30d: int
    median_interval_days: float
