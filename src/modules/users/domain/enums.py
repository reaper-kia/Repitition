from enum import StrEnum


class Role(StrEnum):
    CLIENT = "client"
    CLIENT_MANAGER = "client_manager"
    ADMIN = "admin"