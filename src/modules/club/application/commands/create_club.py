from dataclasses import dataclass


@dataclass
class CreateClubCommand:
    name: str
