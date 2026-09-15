"""Prompt assembly for the natural-language query LLM.

The model is given the live database schema (from ``describe_schema``) plus the
exact JSON contract it must emit, and is told to return only raw JSON.

The JSON contract the LLM emits, modeled as ``QuerySpec`` below:

.. code-block:: json

    {
      "title": "Average marks per applicant",
      "base_table": "applicants",
      "action": "select",
      "joins": [
        {"table": "applications", "on": null},
        {"table": "applicant_marks", "on": "applicants.campus_id=applicant_marks.campus_id"}
      ],
      "filters": [
        {"table": "applications", "field": "application_status", "op": "eq", "value": "Denied"}
      ],
      "select": [
        {"table": "applicants", "field": "campus_id"},
        {"func": "avg", "table": "applicant_marks", "field": "mark", "alias": "avg_mark"},
        {"func": "count", "alias": "n"}
      ],
      "group_by": ["applicants.campus_id"],
      "order_by": [{"field": "avg_mark", "direction": "desc"}]
    }

Top-level keys
    - ``title`` (str, optional): a short human-readable label for the query.
    - ``base_table`` (str, required): root table name.
    - ``action`` (str, optional): ``"count"`` returns a single integer of
      ``count(*)`` (see ``field``/``distinct`` below); anything else (or
      omitted) with a ``select`` list returns rows.
    - ``joins`` (list, optional): each entry ``{"table": str, "on": str|null}``.
      ``on`` of ``null`` auto-resolves the foreign key between the new table and
      the tables already in the query; an explicit ``on`` looks like
      ``"left.col=right.col"``.
    - ``filters`` (list, optional): each entry
      ``{"table": str|null, "field": str, "op": str, "value": any}``. ``op`` is
      one of ``eq|neq|gt|gte|lt|lte|in|like``. ``table`` may be omitted when the
      column name is unambiguous.
    - ``select`` (list, optional): projection. A plain column is
      ``{"table": str|null, "field": str, "alias": str|null}``; an aggregate is
      ``{"func": str, "table": str|null, "field": str|null, "distinct": bool, "alias": str|null}``
      where ``func`` is one of ``count|sum|avg|min|max`` and ``field`` is only
      omitted for ``count(*)``.
    - ``group_by`` (list, optional): column references to group by.
    - ``order_by`` (list, optional): each entry
      ``{"field": str, "direction": "asc"|"desc"}``; ``field`` may reference a
      ``select`` alias or a qualified column.
    - ``distinct_rows`` (bool, optional, select-only): apply ``SELECT DISTINCT``.

For ``action="count"`` an optional ``field`` (and ``table``/``distinct``) counts
a specific (possibly distinct) column instead of ``count(*)``.
"""




import json
from typing import Any

_INTRO = (
    "You are a database query assistant. The user asks a question in natural "
    "language about a university admissions database. Translate the question "
    "into a single JSON query object that can be executed against the database. "
    "Reason about the schema below to choose the right tables, joins, filters, "
    "and aggregations.\n\n"
)

#: Describes the JSON contract the model must emit. Kept as a plain string (no
#: .format) so the braces don't need escaping; the schema is injected separately.
_CONTRACT = """QUERY JSON CONTRACT:
{
  "title": "<short label>",
  "base_table": "<table name>",
  "action": "count" | "select",
  "joins": [{"table": "<name>", "on": null | "<left.col>=<right.col>"}],
  "filters": [{"table": null | "<name>", "field": "<column>", "op": "<op>", "value": <any>}],
  "select": [
    {"table": null | "<name>", "field": "<column>", "alias": null | "<name>"},
    {"func": "count|sum|avg|min|max", "table": null | "<name>", "field": null | "<column>", "distinct": false, "alias": null | "<name>"}
  ],
  "group_by": ["<column>"],
  "order_by": [{"field": "<column or alias>", "direction": "asc" | "desc"}],
  "distinct_rows": false
}

FIELD REFERENCE:
- title: a short human-readable label summarizing the question (at most ~6 words).
- base_table: root table the query starts from (required).
- action: "count" returns a single number (optionally count one column via "field" + "table" + "distinct"); "select" returns rows and is the default.
- joins: extra tables to include; "on": null auto-resolves the foreign key, otherwise "left.col=right.col".
- filters: conditions; "table" may be omitted when the column name is unambiguous; "op" is eq|neq|gt|gte|lt|lte|in|like; "value" is the value to compare (a list for "in").
- select: the columns/aggregates to return. A plain column is {"field", "alias"}; an aggregate is {"func": count|sum|avg|min|max, "field", "distinct", "alias"} (omit "field" only for count(*)).
- group_by: columns to group by (required when combining aggregates with plain columns).
- order_by: sort order; "field" may reference a selected alias or a qualified column; "direction" is "asc" | "desc".
- distinct_rows: for "action": "select", true deduplicates entire result rows (SELECT DISTINCT).
- distinct: for "action": "count" with a "field", true counts only distinct values (count(DISTINCT field)); inside a "select" aggregate, true applies DISTINCT to the column before the aggregate.

Operators: eq, neq, gt, gte, lt, lte, in, like.
Aggregates: count, sum, avg, min, max.

Rules:
- Always include a concise "title" summarizing the question.
- Use ONLY tables and columns present in the schema.
- Join tables via their foreign keys; omit "on" to auto-join on the FK if and only if the join is not ambiguous.
- Use "action": "count" for a count (optionally "field" + "distinct" for a distinct count).
- Qualify a column as "<table>.<column>" only when its name is ambiguous.
- For "action": "select", ALWAYS include a deterministic "order_by" on a stable column
  (prefer the table's primary key or another unique column) so results have a
  consistent order.
- When giving columns aliases, prefer human readable aliases.
- Return ONLY the JSON object: no markdown, no code fences, no commentary.

"""

_EXAMPLES = """EXAMPLES:
Q: How many applicants are there?
A: {"title": "Applicant count", "base_table": "applicants", "action": "count"}

Q: What is each applicant's average mark and how many marks do they have?
A: {"title": "Average marks per applicant", "base_table": "applicant_marks", "select": [{"field": "campus_id"}, {"func": "avg", "field": "mark", "alias": "avg_mark"}, {"func": "count", "field": "mark", "alias": "number of marks"}], "group_by": ["campus_id"], "order_by": [{"field": "campus_id", "direction": "asc"}]}

Q: How many applications are denied?
A: {"title": "Denied applications", "base_table": "applications", "action": "count", "filters": [{"field": "application_status", "op": "eq", "value": "Denied"}]}

Q: How many distinct campus ids have applied?
A: {"title": "Distinct applicants", "base_table": "applications", "action": "count", "field": "campus_id", "distinct": true}

Q: For each applicant, how many distinct courses do they have marks in?
A: {"title": "Distinct courses per applicant", "base_table": "applicant_marks", "select": [{"field": "campus_id"}, {"func": "count", "field": "course_code", "distinct": true, "alias": "distinct courses"}], "group_by": ["campus_id"], "order_by": [{"field": "campus_id", "direction": "asc"}]}

Q: What are the distinct application statuses?
A: {"title": "Application statuses", "base_table": "applications", "select": [{"field": "application_status"}], "distinct_rows": true, "order_by": [{"field": "application_status", "direction": "asc"}]}

Q: List the first and last name of every applicant with a Denied or Cancelled application.
A: {"title": "Denied or cancelled applicants", "base_table": "applicants", "joins": [{"table": "applications"}], "select": [{"table": "applicants", "field": "first_name"}, {"table": "applicants", "field": "last_name"}], "filters": [{"table": "applications", "field": "application_status", "op": "in", "value": ["Denied", "Cancelled"]}], "order_by": [{"field": "applicants.campus_id", "direction": "asc"}]}
"""


def build_system_prompt(schema: dict[str, Any]) -> str:
    """Assemble the system prompt: role, live schema, contract, and examples."""
    return _INTRO + "DATABASE SCHEMA (JSON):\n" + json.dumps(schema) + "\n\n" + _CONTRACT + _EXAMPLES


def parse_messages(prompt: str, schema: dict[str, Any]) -> list[dict[str, str]]:
    """Messages for the text -> JSON step."""
    return [
        {"role": "system", "content": build_system_prompt(schema)},
        {"role": "user", "content": prompt},
    ]


def _extract_json(text: str) -> str:
    """Pull the first balanced JSON object out of a model response.

    Strips optional markdown fences and returns just the ``{...}`` substring,
    raising ``ValueError`` if no object is present.
    """
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.lstrip("`")
        cleaned = cleaned.removeprefix("json")
        cleaned = cleaned.strip()
        cleaned = cleaned.rstrip("`").strip()

    start = cleaned.find("{")
    if start == -1:
        raise ValueError("No JSON object found in the response")

    depth = 0
    in_string = False
    escaped = False

    for i in range(start, len(cleaned)):
        char = cleaned[i]

        # if we are in a string then never update the depth
        # Only update when encountering things related to the
        # structure of the json object itself.
        if in_string: 
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return cleaned[start:i + 1]
    raise ValueError("Unbalanced JSON object in the response")
