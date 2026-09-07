class ChallengeNotFoundError(Exception):
    """Программа онбординга не найдена."""


class ChallengeAlreadyPublishedError(Exception):
    """Опубликованную версию нельзя менять — создавайте следующую."""


class StageAlreadyCompletedError(Exception):
    """Этап уже завершён: повторная обработка не выдаёт вторую награду."""


class AchievementAlreadyGrantedError(Exception):
    """Ачивка с таким source_key уже выдана."""


class RetentionCaseAlreadyResolvedError(Exception):
    """По кейсу уже принято решение."""


class DuplicateOpenCaseError(Exception):
    """У клиента уже есть открытый кейс этого типа."""
