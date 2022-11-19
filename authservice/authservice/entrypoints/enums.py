import enum


class StrEnum(str, enum.Enum):
    """Parent Custom Enum Str"""

    def __new__(cls, value: str, phrase: str):
        obj = str.__new__(cls, value)
        obj._value_ = value

        obj.phrase = phrase

        return obj

    @classmethod
    def choices(cls):
        return [
            dict(
                key=attr.value,
                name=attr.phrase,
            )
            for attr in list(cls)
        ]


class UserRole(StrEnum):
    """User Role"""

    ADMIN = "admin", "Администратор"
    USER = "user", "Пользователь"


class ServiceProvider(enum.Enum):
    VK = "vk"
    YANDEX = "yandex"
