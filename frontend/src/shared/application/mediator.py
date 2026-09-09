from dataclasses import dataclass, field
from typing import Any


@dataclass
class Mediator:
    _handlers: dict[type[Any], Any] = field(default_factory=dict)

    def register(self, message_type: type[Any], handler: Any):
        self._handlers[message_type] = handler

    async def send(self, message: Any) -> Any:
        message_type = type(message)

        handler = self._handlers.get(message_type)
        if not handler:
            raise RuntimeError(f"No handler for message type {message_type.__name__}")

        return await handler.handle(message)
