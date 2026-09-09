from src.modules.visit.application.commands.close_visit import CloseVisitCommand
from src.modules.visit.domain.entities import Visit
from src.modules.visit.domain.exceptions import VisitNotFoundError, VisitAlreadyClosedError
from src.shared.application.unit_of_work import UnitOfWork

class CloseVisitHandler:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def handle(self, cmd: CloseVisitCommand) -> Visit:
        async with self._uow as uow:
            # 1. Поиск визита
            visit = await uow.visits.get_by_external_id(cmd.external_id)
            if not visit:
                raise VisitNotFoundError(f"Visit with external_id {cmd.external_id} not found")

            # 2. Проверка, не закрыт ли он уже (защита от двойного прохода на выход)
            if visit.exited_at is not None:
                raise VisitAlreadyClosedError("Visit is already closed")

            # 3. Изменение состояния (бизнес-правило живёт в домене)
            visit.close(cmd.exited_at)

            # 4. Сохранение изменений 
            # В SQLAlchemy объект уже в сессии, но для явности вызываем add (или save)
            await uow.visits.add(visit) 

            # 5. Коммит транзакции
            await uow.commit()

            return visit