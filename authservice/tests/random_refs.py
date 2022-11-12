import datetime
import random

from faker import Faker

from authservice.database import models
from authservice.entrypoints import enums

f = Faker()


def random_users():
    """Generate users data"""

    return [
        dict(
            login=f.email(),
            full_name=f.bothify(
                text="??????-##", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            ),
            patronymic=f.bothify(
                text="??????-##", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            ),
            role=random.choice(
                [
                    enums.UserRole.ADMIN.value,
                    enums.UserRole.USER.value,
                ]
            ),
        )
        for _ in range(10)
    ]