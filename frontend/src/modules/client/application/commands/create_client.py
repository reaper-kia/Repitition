from dataclasses import dataclass


@dataclass
class CreateClientCommand:
    name: str
