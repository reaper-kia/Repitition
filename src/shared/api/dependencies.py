# Предполагаем, что фабрика сессий определена в shared/infra/database/session.py
from src.shared.infra.database.unit_of_work import SQLAlchemyUnitOfWork
from src.shared.infra.database.session import async_session_maker
from src.shared.application.unit_of_work import UnitOfWorkFactory


def get_unit_of_work_factory() -> UnitOfWorkFactory:
    session_factory = async_session_maker
    return lambda: SQLAlchemyUnitOfWork(session_factory)
