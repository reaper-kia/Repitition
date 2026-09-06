from dataclasses import dataclass

from src.core.config import settings  # <-- импортируем настройки
from src.modules.users.application.commands.register_user import RegisterUserCommand
from src.modules.users.application.ports.password_hasher import PasswordHasher
from src.modules.users.domain.entities import User
from src.modules.users.domain.exceptions import EmailAlreadyExistError
from src.modules.users.domain.value_objects import Email, UserName, RawPassword
from src.shared.application.unit_of_work import UnitOfWorkFactory


@dataclass
class RegisterUserCommandHandler:
    uow_factory: UnitOfWorkFactory
    password_hasher: PasswordHasher

    async def handle(self, cmd: RegisterUserCommand) -> User:
        is_admin = False
        if cmd.admin_code and cmd.admin_code == settings.admin_registration_code:
            is_admin = True

        email = Email(cmd.email)
        name = UserName(cmd.name)
        raw_password = RawPassword(cmd.password)

        async with self.uow_factory() as uow:
            existing_user = await uow.users.get_by_email(email)
            if existing_user:
                raise EmailAlreadyExistError("Email already registered")

            password_hash = self.password_hasher.hash(raw_password.value)

            user = User.register(
                name=name,
                email=email,
                password_hash=password_hash,
                is_admin=is_admin,
            )

            await uow.users.add(user)
            await uow.commit()

        return user
