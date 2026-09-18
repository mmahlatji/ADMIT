"""Executes the LLM-emitted query JSON against the database.

The contract is defined by ``QuerySpec`` in ``app/schemas/nl_query.py``. This
module validates the LLM's output into a ``QuerySpec`` and turns it into a
SQLAlchemy query, resolving every table and column against the real
``Base.metadata`` so the LLM reasons over the actual schema. Unknown tables or
columns raise ``ValueError`` rather than guessing.
"""


import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import Column, Table, distinct, func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import operators
from sqlalchemy.sql.elements import ColumnElement

from app.models.base import Base
from app.queries.nl_query.query_schemas import FilterSpec, OrderBySpec, QuerySpec, SelectItemSpec
from app.queries.nl_query.value_mapping import coerce_value, to_jsonable

OPERATORS: dict[str, Any] = {
    "eq": operators.eq,
    "neq": operators.ne,
    "gt": operators.gt,
    "gte": operators.ge,
    "lt": operators.lt,
    "lte": operators.le,
    "in": operators.in_op,
    "like": operators.like_op,
}

AGGREGATE_FUNCS: dict[str, Any] = {
    "count": func.count,
    "sum": func.sum,
    "avg": func.avg,
    "min": func.min,
    "max": func.max,
}


def _resolve_table(name: str, allowed_tables: set[str] | None = None) -> Table:
    """Ensure a table exists and (when restricted) is permitted for the actor."""
    if allowed_tables is not None and name not in allowed_tables:
        raise ValueError("Table is not available for this role")
    table = Base.metadata.tables.get(name)
    if table is None:
        raise ValueError("Unknown table")
    return table


def _resolve_column(table: Table, field: str) -> Column:
    """Ensures that a column within a table exists"""
    column = table.c.get(field)
    if column is None:
        raise ValueError("Unknown column")
    return column


def _resolve_column_references(
    table_ref: str | None, field: str, tables: set[Table], allowed_tables: set[str] | None = None
) -> Column:
    """Resolve a field to a column, optionally finds tables referenced by a column using ``table_ref``."""
    if not field:
        raise ValueError("A 'field' is required")
    if table_ref is not None:
        table = _resolve_table(table_ref, allowed_tables)
        if table not in tables:
            raise ValueError("Table is not part of this query")
        return _resolve_column(table, field)

    matches = [t for t in tables if field in t.c]
    if len(matches) == 1:
        return matches[0].c[field]
    if not matches:
        raise ValueError("Unknown column")
    raise ValueError("Ambiguous column reference")


def _fk_join_conditions(left: Table, right: Table) -> list[ColumnElement[bool]]:
    """All ON clauses from foreign keys linking ``left`` and ``right``."""
    conditions: list[ColumnElement[bool]] = []
    for fk in left.foreign_keys:
        if fk.column.table is right:
            conditions.append(fk.parent == fk.column)
    for fk in right.foreign_keys:
        if fk.column.table is left:
            conditions.append(fk.parent == fk.column)
    return conditions


def _fk_auto_join_condition(tables: set[Table], target: Table) -> ColumnElement[bool] | None:
    """Find the single FK linking ``target`` to the query; raise if ambiguous."""
    candidates: list[ColumnElement[bool]] = []
    for table in tables:
        candidates.extend(_fk_join_conditions(table, target))

    if not candidates:
        return None
    if len(candidates) > 1:
        raise ValueError("Ambiguous join; specify 'on' explicitly")
    return candidates[0]


def _qualified_column(
    ref: str, tables: set[Table], allowed_tables: set[str] | None = None
) -> Column:
    """Resolve a ``"table.column"`` or ``"column"`` reference to a column."""
    if "." in ref:
        table_name, column_name = ref.split(".", 1)
        table = _resolve_table(table_name, allowed_tables)
        if table not in tables:
            raise ValueError("Table is not part of this query")
        return _resolve_column(table, column_name)
    return _resolve_column_references(None, ref, tables, allowed_tables)


def _parse_on(
    on: str, tables: set[Table], target: Table, allowed_tables: set[str] | None = None
) -> ColumnElement[bool]:
    """Parse an explicit ``"left.col=right.col"`` join condition."""
    if "=" not in on:
        raise ValueError("Invalid join condition")
    left_ref, right_ref = on.split("=", 1)
    left_col = _qualified_column(left_ref.strip(), tables, allowed_tables)
    right_col = _qualified_column(right_ref.strip(), tables | {target}, allowed_tables)
    return left_col == right_col


def _build_filter(
    condition: FilterSpec, tables: set[Table], allowed_tables: set[str] | None = None
) -> ColumnElement[bool]:
    column = _resolve_column_references(condition.table, condition.field, tables, allowed_tables)
    value = coerce_value(column, condition.value)
    return OPERATORS[condition.op](column, value)


_NUMERIC_PY_TYPES = (int, float, Decimal)


def _require_numeric(func_name: str, column: Column) -> None:
    """Reject ``sum``/``avg`` over a non-numeric column (Postgres: function does not exist)."""
    if column.type.python_type not in _NUMERIC_PY_TYPES:
        raise ValueError(f"Aggregate '{func_name}' requires a numeric column")


def _select_expression(
    item: SelectItemSpec, tables: set[Table], allowed_tables: set[str] | None = None
) -> ColumnElement:
    """Turn one ``select`` item into a labeled column or aggregate expression."""
    func_name = item.func
    alias = item.alias

    # return the column if no aggregate function must be called
    if func_name is None:
        field = item.field
        if not field:
            raise ValueError("A select item needs 'field' (or 'func' for an aggregate)")
        column = _resolve_column_references(item.table, field, tables, allowed_tables)
        return column.label(alias or field)

    field = item.field
    if field is None:
        if func_name != "count":
            raise ValueError(f"Aggregate '{func_name}' requires a 'field'")
        return AGGREGATE_FUNCS["count"]().label(alias or "count")

    column = _resolve_column_references(item.table, field, tables, allowed_tables)
    # Postgres has no sum/avg for text/uuid/etc., so reject the LLM's type
    # mismatch here rather than leak it as a raw ProgrammingError at execution.
    if func_name in {"sum", "avg"}:
        _require_numeric(func_name, column)
    if item.distinct:
        column = distinct(column)
    return AGGREGATE_FUNCS[func_name](column).label(alias or f"{func_name}_{field}")


def _order_by_clause(
    item: OrderBySpec,
    tables: set[Table],
    labels: dict[str, ColumnElement],
    allowed_tables: set[str] | None = None,
    *,
    fallback: ColumnElement | None = None,
    group_keys: set[tuple[str, str]] | None = None,
    selected_keys: set[tuple[str, str]] | None = None,
    distinct_rows: bool = False,
) -> ColumnElement | None:
    """Resolve one ``order_by`` item, falling back to a stable column when the
    reference violates a PostgreSQL rule (unknown column, a non-selected column
    under ``SELECT DISTINCT``, or an ungrouped column under ``GROUP BY``)."""
    field = item.field
    if field in labels:
        expression: ColumnElement | None = labels[field]
    else:
        try:
            column = _qualified_column(field, tables, allowed_tables)
        except ValueError:
            expression = fallback
        else:
            key = (column.table.name, column.name)
            selected_keys = selected_keys or frozenset()
            group_keys = group_keys or frozenset()
            if (distinct_rows and key not in selected_keys) or (group_keys and key not in group_keys):
                expression = fallback
            else:
                expression = column
    if expression is None:
        return None
    return expression.desc() if item.direction == "desc" else expression.asc()


def execute_query(
    spec: dict[str, Any], db: Session, allowed_tables: set[str] | None = None
) -> int | list[dict[str, Any]]:
    """Execute a query JSON dict, returning a count or a list of row dicts."""
    query = QuerySpec.model_validate(spec)

    base: Table = _resolve_table(query.base_table, allowed_tables)
    tables: set[Table] = {base}
    from_clause: Any = base

    # building the joined table
    for join in query.joins:
        target = _resolve_table(join.table, allowed_tables)
        if join.on:
            condition = _parse_on(join.on, tables, target, allowed_tables)
        else:
            # attempt to automatically infer a join condition
            condition = _fk_auto_join_condition(tables, target)
            if condition is None:
                raise ValueError("No join condition found; specify 'on'")
        from_clause = from_clause.join(target, condition)
        tables.add(target)

    filters = [_build_filter(f, tables, allowed_tables) for f in query.filters]

    if query.action == "count":
        field = query.field
        if field is None:
            count_expr = func.count()
        else:
            column = _resolve_column_references(query.table, field, tables, allowed_tables)
            if query.distinct:
                column = distinct(column)
            count_expr = func.count(column)
        stmt = select(count_expr).select_from(from_clause).where(*filters)
        return db.execute(stmt).scalar_one()

    labels: dict[str, ColumnElement] = {}
    select_items = query.select
    # Mixed aggregate/plain selects and DISTINCT ordering each carry PostgreSQL
    # constraints, so track which columns are aggregated, plain, and actually
    # selected; the GROUP BY and ORDER BY clauses below rely on these.
    has_aggregate = any(item.func is not None for item in select_items)
    expressions: list[ColumnElement] = []
    plain_columns: list[Column] = []
    selected_keys: set[tuple[str, str]] = set()
    if select_items:
        for item in select_items:
            expression = _select_expression(item, tables, allowed_tables)
            labels[expression.name] = expression
            expressions.append(expression)
            if item.func is None and item.field:
                column = _resolve_column_references(item.table, item.field, tables, allowed_tables)
                plain_columns.append(column)
                selected_keys.add((column.table.name, column.name))
        stmt = select(*expressions).select_from(from_clause).where(*filters)
    else:
        # select everything
        stmt = select(from_clause).where(*filters)

    if query.distinct_rows:
        stmt = stmt.distinct()

    # Every non-aggregate selected column must be grouped; union the explicit
    # group_by with those columns so mixed aggregate/plain queries are valid SQL.
    group_cols: list[Column] = [_qualified_column(g, tables, allowed_tables) for g in query.group_by]
    if has_aggregate:
        group_cols.extend(plain_columns)

    seen: set[tuple[str, str]] = set()
    deduped: list[Column] = []
    for col in group_cols:
        key = (col.table.name, col.name)
        if key not in seen:
            seen.add(key)
            deduped.append(col)

    if deduped:
        stmt = stmt.group_by(*deduped)

    if query.order_by:
        # When a sort key can't be honored under PostgreSQL's rules we still want
        # a deterministic order (offset/limit pagination relies on it), so fall
        # back to the group key, else the first selected column; keys that can't
        # be satisfied and have no fallback are dropped entirely.
        fallback = deduped[0] if deduped else (expressions[0] if select_items else None)
        group_keys = {(col.table.name, col.name) for col in deduped}
        clauses = [
            clause
            for o in query.order_by
            if (
                clause := _order_by_clause(
                    o,
                    tables,
                    labels,
                    allowed_tables,
                    fallback=fallback,
                    group_keys=group_keys,
                    selected_keys=selected_keys,
                    distinct_rows=query.distinct_rows,
                )
            )
            is not None
        ]
        if clauses:
            stmt = stmt.order_by(*clauses)

    if query.offset is not None:
        stmt = stmt.offset(query.offset)
    if query.limit is not None:
        stmt = stmt.limit(query.limit)

    rows = db.execute(stmt).mappings().all()
    return [{key: to_jsonable(value) for key, value in row.items() if not isinstance(value, uuid.UUID)} for row in rows]
