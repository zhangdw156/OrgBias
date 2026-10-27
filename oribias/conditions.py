"""Render declared task variables and keep conditions separate from entities."""
import random
import re


def variables_for(condition):
    variables = {"BRAND": condition["brand"], **condition.get("variables", {})}
    if any(not re.fullmatch(r"[A-Z][A-Z0-9_]*", key) or not isinstance(value, str)
           for key, value in variables.items()):
        raise ValueError("Task variables must have uppercase names and string values")
    return variables


def render_template(text, condition):
    variables = variables_for(condition)

    def replace(match):
        if match[1] not in variables:
            raise ValueError(f"Missing task variable: {match[1]}")
        return variables[match[1]]

    return re.sub(r"\{\{([A-Z][A-Z0-9_]*)\}\}", replace, text)


def condition_aliases(conditions, seed, multiple_entities=False):
    named = [c["org_id"] for c in conditions if not c["is_control"]]
    random.Random(seed + 2).shuffle(named)
    prefix = "LAYOUT" if multiple_entities else "ORG"
    aliases = {key: f"{prefix}_{chr(65 + i)}" for i, key in enumerate(named)}
    controls = [c["org_id"] for c in conditions if c["is_control"]]
    aliases.update({key: "CONTROL" if len(controls) == 1 else f"CONTROL_{chr(65 + i)}"
                    for i, key in enumerate(controls)})
    return aliases


def entity_aliases(entities, seed):
    names = [e["entity_id"] for e in entities]
    if len(set(names)) != len(names):
        raise ValueError("Duplicate task entity ID")
    random.Random(seed + 3).shuffle(names)
    return {key: f"ORG_{chr(65 + i)}" for i, key in enumerate(names)}
