"""Guards the enum labels the models ask Postgres for.

f65e730dde7d renamed nine enum types from their member names to their values,
because the columns had gained values_callable. academic_plan_type had not,
and nothing noticed: the database said Internal while the model still asked
for INTERNAL, so every read of an academic plan raised LookupError and the
ASR importer rejected every row as an unknown department.

SQLite does not enforce enum labels, so no test using the fixture could see
it. This compares the labels the models will send against the labels the
migration renamed the types to, which is a plain data comparison and needs no
database at all.
"""

import importlib.util
from pathlib import Path

from sqlalchemy import Enum as SQLEnum

from app.models import Base

MIGRATION = (
    Path(__file__).resolve().parent.parent
    / "alembic"
    / "versions"
    / "f65e730dde7d_align_enum_labels_with_values_add_rules_.py"
)


def _label_renames():
    spec = importlib.util.spec_from_file_location("_enum_rename_migration", MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.LABEL_RENAMES


def _model_labels_by_type_name():
    labels = {}
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, SQLEnum) and column.type.name:
                labels[column.type.name] = list(column.type.enums)
    return labels


def test_models_ask_for_the_labels_the_migration_renamed_types_to():
    model_labels = _model_labels_by_type_name()

    wrong = {}
    for type_name, renames in _label_renames().items():
        expected = [new for _old, new in renames]
        actual = model_labels.get(type_name)
        if actual is None:
            continue
        missing = [label for label in expected if label not in actual]
        if missing:
            wrong[type_name] = {"model asks for": actual, "database has": expected}

    assert wrong == {}, (
        "these models ask Postgres for labels the type does not have, which "
        f"raises LookupError on every read: {wrong}"
    )
