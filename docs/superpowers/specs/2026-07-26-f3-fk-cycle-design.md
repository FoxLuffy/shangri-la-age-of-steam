# F3 — Resolve character↔guild FK Cycle Design

Roadmap item: **F3** (Housekeeping). SQLAlchemy emits, on `drop_all`:
`SAWarning: Can't sort tables for DROP; an unresolvable foreign key dependency exists
between tables: character, guild`.

## Cause
- `Character.guild_id` → `guild.id` (optional, indexed).
- `Guild.leader_id` → `character.id` (required).

The mutual foreign keys form a cycle, so SQLAlchemy can't topologically order table
creation/drop and warns.

## Fix
Mark one edge of the cycle with `use_alter=True` so its foreign key is emitted via a
separate `ALTER TABLE`, breaking the ordering dependency. Convert `Guild.leader_id`
(the non-indexed edge) to an explicit column:
```python
leader_id: int = Field(
    sa_column=Column(
        Integer,
        ForeignKey("character.id", use_alter=True, name="fk_guild_leader_id"),
        nullable=False,
    )
)
```
Add `Integer, ForeignKey` to the `from sqlalchemy import ...` line in `database.py`.

Only the DDL emission strategy changes; runtime FK semantics are identical. SQLite doesn't
enforce FKs by default, so behavior is unchanged. No migration is needed — the schema is
built via `create_all`, and the existing Alembic migrations are baseline stubs.

## Test: `backend/tests/test_fk_cycle.py`
- Under `warnings.catch_warnings(record=True)` with `simplefilter("always")`, run
  `SQLModel.metadata.create_all(engine)` then `drop_all(engine)` and assert **no** captured
  warning message contains "unresolvable foreign key".

## Verification
- Full suite green.
- The FK-cycle `SAWarning` no longer appears (its count across the suite is 0).
- `ruff` clean.

## Acceptance
- No circular-FK DROP warning; guild/character relationships still work; suite green.
