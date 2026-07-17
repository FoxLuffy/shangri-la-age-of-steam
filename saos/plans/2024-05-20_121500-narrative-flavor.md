# Narrative Flavor & Exploration Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Enhance the AI's descriptive depth and ability to handle environmental exploration.

**Architecture:** Implement a multi-layered prompt system that separates "System Instructions" (Persona, Rules), "Contextual State" (Current Location, NPCs, History), and "Input Processing." We will add an "Exploration Model" that allows the AI to describe static environment details when requested.

**Tech Stack:** Python, Pydantic, Jinja2 (for prompt templating)

---

### Task 1: Prompt Templating with Jinja2

**Objective:** Move from f-strings to a more maintainable Jinja2 templating system for prompts.

**Files:**
- Create: `shangri-la-age-of-steam/backend/templates/narrative_prompt.j2`
- Create: `shangri-la-age-of-steam/backend/prompt_utils.py` (Modify to use Jinja2)
- Modify: `shangri-la-age-of-steam/backend/requirements.txt` (Add `jinja2`)

**Step 1: Update Requirements**
Add `jinja2` to `backend/requirements.txt`.

**Step 2: Create Jinja2 Template**
Create `backend/templates/narrative_prompt.j2`:
```jinja2
You are the narrator of "Shangri-la: Age of Steam," a gritty, atmospheric RPG.
Current Location: {{ location.name }} - {{ location.description }}
Active NPCs:
{% for npc in active_npcs %}
- {{ npc.name }}: {{ npc.traits | join(', ') }}
{% endfor %}

Player Action: {{ action_text }}

Task: Describe the results of the action. Include sensory details (smell, sound, temperature). 
If the action leads to a new location, describe the transition.
Output Format:
[Narration]
(Narrative text here)

[StateUpdates]
(JSON-formatted updates if applicable)
```

**Step 3: Update Prompt Builder**
Update `prompt_utils.py` to load this template and render it with current `WorldState` and `PlayerAction`.

**Step 4: Commit**
```bash
git add backend/
git commit -m "feat: implement jinja2 prompt templating"
```

---

### Task 2: Write Failing Flavor Test

**Objective:** Verify that the prompt builder correctly handles diverse inputs (e.g., many NPCs, long action text).

**Files:**
- Create: `shangri-la-age-of-steam/backend/tests/test_flavor_prompts.py`

**Step 1: Write test**
Create a test that passes a `WorldState` with 5+ NPCs and a 200-character action string.
Verify that the generated prompt contains all names and the correct "system instructions" header.

**Step 2: Run test**
Run: `pytest backend/tests/test_flavor_prompts.py -v`

**Step 3: Commit**
```bash
git add backend/
git commit -m "test: add flavor prompt verification"
```

---

### Task 3: Exploration & Mood Logic

**Objective:** Implement a "Mood" parameter and "Exploration" mode in the engine.

**Files:**
- Modify: `shangri-la-age-of-steam/backend/models.py`
- Modify: `shangri-la-age-of-steam/backend/engine.py`

**Step 1: Update Models**
Add `mood: str` and `is_exploration: bool` to `PlayerAction`.

**Step 2: Update Engine**
Modify `NarrativeEngine.process_action` to inject the mood into the prompt. If `is_exploration` is true, append "Provide a detailed description of the surroundings" to the prompt.

**Step 3: Verify and Commit**
Run existing tests and commit.
```bash
git add backend/
git commit -m "feat: add mood and exploration support"
```
