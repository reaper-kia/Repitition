from src.modules.visit.application.commands.record_visit import RecordVisitCommand
from src.modules.visit.domain.entities import Visit
from src.modules.visit.domain.exceptions import ClientSnapshotNotFoundError
from src.shared.application.unit_of_work import UnitOfWork

class RecordVisitHandler:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def handle(self, cmd: RecordVisitCommand) -> Visit:
        async with self._uow as uow:
            # 1. Проверка идемпотентности (защита от дублей от турникета)
            existing_visit = await uow.visits.get_by_external_id(cmd.external_id)
            if existing_visit:
                return existing_visit
            
            client_snapshot = await uow.client_snapshots.get_by_id(cmd.client_id)
            if not client_snapshot:
                raise ClientSnapshotNotFoundError(f"Client {cmd.client_id} not found")
            visit = Visit.record(
                external_id=cmd.external_id,
                client_id=cmd.client_id,
                club_id=cmd.club_id,
                entered_at=cmd.entered_at,
            )

            # 4. Сохранение (commit() НЕ вызываем!)
            await uow.visits.add(visit)
            
            # 5. Коммит транзакции (граница транзакции здесь)
            await uow.commit()

            return visit