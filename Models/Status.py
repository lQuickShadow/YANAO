from Models.Base import *


class Status(BaseModel):
    # Фиксированные статусы заявки
    NEW = 1          # Новый
    IN_PROGRESS = 2  # В работе
    DONE = 3         # Завершено

    id = PrimaryKeyField(primary_key=True)
    name = CharField(unique=True)

    class Meta:
        table_name = "status"