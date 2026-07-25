# Modding Guide — Shangri-La: Age of Steam

Add your own **factions, locations, NPCs, and items** to the world with a single JSON
file. This guide covers the mod file format, every supported field, how uploads are
applied, and a ready-to-use template.

> A runnable template lives at [`docs/mods/example_mod.json`](mods/example_mod.json). It
> is exercised by `backend/tests/test_modding_example.py`, so it always matches the
> current loader.

---

## Uploading a mod

Two ways to load a mod file:

- **In game:** open **Settings → Modding (JSON Support) → Upload JSON** and pick your file.
- **API:** `POST /modding/upload` as `multipart/form-data` with a single `file` field:

  ```bash
  curl -X POST http://localhost:8003/modding/upload \
    -F "file=@docs/mods/example_mod.json"
  ```

On success you get `{"status": "success", ...}`. On any error (bad JSON, unknown field,
type mismatch) you get HTTP **400** with a `detail` message, and nothing is saved.

---

## File format

A mod is a single JSON object with any of these **optional** top-level arrays. Include only
the ones you need:

```json
{
  "factions":  [ ... ],
  "locations": [ ... ],
  "npcs":      [ ... ],
  "items":     [ ... ]
}
```

Entities are applied in this order: **factions → locations → npcs → items**. Put a faction
or location in the same file as the NPCs that reference it so the references resolve.

### Upsert behavior

Uploading is **idempotent** and can also edit existing entities:

| Entity    | Matched by | If it exists            | If it doesn't        |
|-----------|------------|-------------------------|----------------------|
| faction   | `id`       | fields overwritten      | created              |
| location  | `id`       | fields overwritten      | created              |
| npc       | `id`       | fields overwritten      | created              |
| item      | `name`     | fields overwritten      | created              |

Because updates overwrite by key, re-uploading a corrected file is safe. Use a unique
prefix (e.g. `mod_`) on your IDs to avoid clobbering base-game content.

---

## Entity reference

Types below mirror the game's data models. **Required** fields must be present; optional
fields fall back to the listed default.

### Faction

| Field         | Type   | Required | Notes                      |
|---------------|--------|----------|----------------------------|
| `id`          | string | yes      | primary key, unique        |
| `name`        | string | yes      |                            |
| `description` | string | yes      |                            |

### Location

| Field         | Type   | Required | Default | Notes                                   |
|---------------|--------|----------|---------|-----------------------------------------|
| `id`          | string | yes      |         | primary key, unique                     |
| `name`        | string | yes      |         |                                         |
| `description` | string | yes      |         |                                         |
| `faction_id`  | string | no       | `null`  | id of a faction that controls it        |

### NPC

| Field                 | Type            | Required | Default | Notes                                        |
|-----------------------|-----------------|----------|---------|----------------------------------------------|
| `id`                  | string          | yes      |         | primary key, unique                          |
| `name`                | string          | yes      |         |                                              |
| `traits`              | string[]        | no       | `[]`    | short descriptors used in prompts            |
| `current_dialogue`    | string          | no       | `null`  | opening line                                 |
| `disposition`         | number          | no       | `0.0`   | −1.0 (hostile) … 1.0 (friendly)              |
| `memories`            | object[]        | no       | `[]`    | list of `{ "key": "...", "value": "..." }`   |
| `location_id`         | string          | no       | `"1"`   | id of an existing location                   |
| `faction_id`          | string          | no       | `null`  | id of an existing faction                    |
| `custom_system_prompt`| string          | no       | `null`  | overrides the NPC's system prompt            |
| `speed`               | integer         | no       | `5`     | combat turn order                            |
| `hp` / `max_hp`       | integer         | no       | `100`   |                                              |
| `armor`               | integer         | no       | `0`     |                                              |
| `status_effects`      | string[]        | no       | `[]`    |                                              |
| `is_hostile`          | boolean         | no       | `false` |                                              |

> `location_id` and `faction_id` should reference entities that already exist or are
> defined earlier in the same file.

### Item

| Field         | Type   | Required | Notes                                        |
|---------------|--------|----------|----------------------------------------------|
| `name`        | string | yes      | match key for upsert                         |
| `description` | string | no       |                                              |
| `category`    | enum   | yes      | one of the categories below                  |

`category` must be exactly one of:

- `Consumables`
- `Equipment`
- `Crafting_Materials`
- `Steam_Tech_Components`

---

## Annotated example

The same content as `docs/mods/example_mod.json`, annotated (JSON itself allows no
comments — strip these before use, or just upload the `.json` file directly):

```jsonc
{
  "factions": [
    {
      "id": "mod_clockwork_cabal",              // unique id, referenced by NPCs/locations
      "name": "The Clockwork Cabal",
      "description": "Rogue tinkers who believe automata deserve free will."
    }
  ],
  "locations": [
    {
      "id": "mod_brass_bazaar",
      "name": "The Brass Bazaar",
      "description": "A cramped, lamp-lit black-market for gears.",
      "faction_id": "mod_clockwork_cabal"       // controlled by the faction above
    }
  ],
  "npcs": [
    {
      "id": "mod_tik_the_tinker",
      "name": "Tik the Tinker",
      "traits": ["inventive", "paranoid"],
      "current_dialogue": "Keep your voice down — the Syndicate has ears everywhere.",
      "disposition": 0.2,                        // slightly friendly
      "location_id": "mod_brass_bazaar",         // must exist / be defined above
      "faction_id": "mod_clockwork_cabal",
      "is_hostile": false
    }
  ],
  "items": [
    {
      "name": "Aether-Tuned Gear",               // items upsert by name
      "description": "A precision gear that hums faintly when aether is near.",
      "category": "Steam_Tech_Components"        // must be a valid ItemCategory
    }
  ]
}
```

---

## Validation rules (current)

The loader today performs light validation:

1. The file must be **valid JSON**.
2. Each entity's keys must be **real fields** on its model — an unknown key or a wrong
   type raises HTTP 400 and aborts the whole upload (nothing is committed).
3. `item.category` must be one of the four enum values.

Stricter, per-field validation with detailed error messages (required-field checks, ID
uniqueness, referential checks, content-safety limits) is tracked as **C8.2 — Mod
validation & sandboxing**.

## Planned (not yet loadable)

These are on the roadmap but **not** handled by `/modding/upload` yet — including them in
a mod file has no effect:

- **Recipes** and **Bounties** as moddable entities.
- Mod **ratings/reviews** (C8.3) and **dependencies/mod chains** (C8.4).

See `ROADMAP.md` section C8 for status.
