
from sqlalchemy import inspect
from app.database import engine

inspector = inspect(engine)

tables = inspector.get_table_names()

print("Таблицы в базе DevSpace:")

for table in tables:
    print(f"\nТаблица: {table}")

    columns = inspector.get_columns(table)
    for column in columns:
        print(f"  - {column['name']}")

    foreign_keys = inspector.get_foreign_keys(table)
    for fk in foreign_keys:
        print(
            f"  Связь: {fk['constrained_columns']} "
            f"-> {fk['referred_table']}.{fk['referred_columns']}"
        )
