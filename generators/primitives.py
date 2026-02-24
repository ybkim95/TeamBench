"""
Shared randomization primitives for task generators.

All primitives accept a seed for deterministic, reproducible generation.
These building blocks are composed by individual task generators.
"""
from __future__ import annotations

import hashlib
import random
import string
from typing import Optional

# ── Name pools (diverse, multi-cultural) ─────────────────────────────────

FIRST_NAMES = [
    "Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Heidi",
    "Ivan", "Judy", "Karl", "Liam", "Mia", "Noah", "Olivia", "Peter",
    "Quinn", "Rose", "Sam", "Tara", "Uma", "Vera", "Will", "Xena",
    "Yuki", "Zara", "Amir", "Bina", "Carlos", "Devi", "Elena", "Faisal",
    "Gita", "Hassan", "Ingrid", "Jin", "Kenji", "Luna", "Marco", "Nadia",
    "Omar", "Priya", "Rashid", "Sofia", "Tariq", "Ursula", "Viktor",
    "Wen", "Xavier", "Yara", "Zane", "Akira", "Bianca", "Chen",
    "Deepa", "Emeka", "Fatima", "Gustavo", "Hana", "Idris", "Jing",
    "Kofi", "Leila", "Miguel", "Nneka", "Olga", "Pavel", "Qi",
    "Ravi", "Suki", "Tomás", "Ugo", "Vanya", "Wafa", "Xiomara",
    "Yosef", "Zuri", "Aaliya", "Boris", "Camila", "Dmitri", "Esme",
    "Feng", "Gael", "Hiroshi", "Isla", "Jamal", "Kira", "Leo",
    "Mei", "Nico", "Opal", "Raj", "Soren", "Thea", "Ulric",
    "Violet", "Wyatt", "Yusuf", "Zoe", "Atlas", "Briar", "Cleo",
]

DEPARTMENTS = [
    "sales", "engineering", "marketing", "finance", "operations",
    "hr", "legal", "support", "product", "design", "research",
    "logistics", "compliance", "analytics", "infrastructure",
]

CATEGORIES = [
    "sales", "engineering", "marketing", "finance", "operations",
    "support", "product", "design", "research", "logistics",
]

PROJECT_NAMES = [
    "Titan", "Phoenix", "Neptune", "Aurora", "Zenith", "Nexus",
    "Horizon", "Catalyst", "Quantum", "Apex", "Meridian", "Vertex",
    "Solaris", "Vanguard", "Pinnacle", "Echelon", "Prism",
    "Beacon", "Frontier", "Orbit", "Cascade", "Forge", "Pulse",
    "Summit", "Nova", "Stratos", "Ember", "Helix", "Lumen", "Crest",
]

CODENAMES = [
    "Kestrel", "Falcon", "Osprey", "Condor", "Hawk", "Eagle",
    "Merlin", "Peregrine", "Sparrow", "Raven", "Phoenix", "Griffin",
    "Wyvern", "Drake", "Pegasus", "Chimera", "Hydra", "Kraken",
    "Basilisk", "Cerberus", "Sphinx", "Minotaur", "Leviathan",
    "Behemoth", "Garuda", "Thunderbird", "Simurgh", "Zephyr",
]


class SeededRandom:
    """Deterministic random number generator wrapping Python's random module."""

    def __init__(self, seed: int):
        self._rng = random.Random(seed)

    def randint(self, a: int, b: int) -> int:
        return self._rng.randint(a, b)

    def uniform(self, a: float, b: float) -> float:
        return self._rng.uniform(a, b)

    def choice(self, seq: list):
        return self._rng.choice(seq)

    def sample(self, population: list, k: int) -> list:
        return self._rng.sample(population, k)

    def shuffle(self, lst: list) -> None:
        self._rng.shuffle(lst)

    def random(self) -> float:
        return self._rng.random()


class NamePool:
    """Generate unique person names from a seed."""

    def __init__(self, seed: int, count: int = 30):
        rng = SeededRandom(seed)
        self._names = rng.sample(FIRST_NAMES, min(count, len(FIRST_NAMES)))
        self._idx = 0

    def next(self) -> str:
        name = self._names[self._idx % len(self._names)]
        self._idx += 1
        return name

    def get(self, n: int) -> list[str]:
        return [self.next() for _ in range(n)]


class ValuePool:
    """Generate numeric values from a seed within a range."""

    def __init__(self, seed: int, low: int = 50, high: int = 999):
        self._rng = SeededRandom(seed)
        self._low = low
        self._high = high

    def next(self) -> int:
        return self._rng.randint(self._low, self._high)

    def get(self, n: int) -> list[int]:
        return [self.next() for _ in range(n)]

    def next_float(self, decimals: int = 2) -> float:
        return round(self._rng.uniform(self._low, self._high), decimals)


class CategoryPool:
    """Generate category strings from a seed."""

    def __init__(self, seed: int, pool: list[str] | None = None, count: int = 5):
        rng = SeededRandom(seed)
        src = pool or CATEGORIES
        self._categories = rng.sample(src, min(count, len(src)))

    def next(self) -> str:
        rng = random.Random()
        return rng.choice(self._categories)

    def get_all(self) -> list[str]:
        return list(self._categories)

    def choice(self, rng: SeededRandom) -> str:
        return rng.choice(self._categories)


class BudgetGenerator:
    """Generate realistic budget/monetary values."""

    def __init__(self, seed: int):
        self._rng = SeededRandom(seed)

    def amount(self, scale: str = "millions") -> tuple[float, str]:
        """Returns (numeric_value, formatted_string)."""
        if scale == "millions":
            val = round(self._rng.uniform(1.0, 99.0), 1)
            return val, f"${val}M"
        elif scale == "thousands":
            val = self._rng.randint(10, 999) * 10
            return val, f"${val:,}"
        else:
            val = self._rng.randint(100, 9999)
            return val, f"${val}"


class ConfigMutator:
    """Generate config values with intentional policy violations."""

    def __init__(self, seed: int):
        self._rng = SeededRandom(seed)

    def valid_config(self, schema: dict[str, dict]) -> dict:
        """Generate a config that satisfies all constraints."""
        config = {}
        for key, spec in schema.items():
            if spec["type"] == "int_range":
                config[key] = self._rng.randint(spec["min"], spec["max"])
            elif spec["type"] == "exact_int":
                config[key] = spec["value"]
            elif spec["type"] == "exact_bool":
                config[key] = spec["value"]
            elif spec["type"] == "enum":
                config[key] = self._rng.choice(spec["allowed"])
            elif spec["type"] == "exact_list":
                config[key] = spec["value"]
            elif spec["type"] == "exact_string":
                config[key] = spec["value"]
        return config

    def violated_config(self, schema: dict[str, dict], num_violations: int = 3) -> dict:
        """Generate a config with intentional violations."""
        config = self.valid_config(schema)
        keys = list(schema.keys())
        self._rng.shuffle(keys)

        violations = 0
        for key in keys:
            if violations >= num_violations:
                break
            spec = schema[key]
            if spec["type"] == "int_range":
                # Violate by going out of range
                if self._rng.random() > 0.5:
                    config[key] = spec["max"] + self._rng.randint(1, 100)
                else:
                    config[key] = max(0, spec["min"] - self._rng.randint(1, 50))
                violations += 1
            elif spec["type"] == "exact_int":
                config[key] = spec["value"] + self._rng.randint(1, 10)
                violations += 1
            elif spec["type"] == "exact_bool":
                config[key] = not spec["value"]
                violations += 1
            elif spec["type"] == "enum":
                bad_vals = [v for v in spec.get("all_values", ["info", "debug"]) if v not in spec["allowed"]]
                if bad_vals:
                    config[key] = self._rng.choice(bad_vals)
                    violations += 1
        return config


class ColumnSchemaGenerator:
    """Generate CSV column schemas with drift patterns."""

    def __init__(self, seed: int):
        self._rng = SeededRandom(seed)

    def canonical_columns(self) -> list[str]:
        """The target output schema."""
        return ["id", "name", "value", "category"]

    def generate_rename_map(self) -> dict[str, str]:
        """Generate plausible column renames."""
        rename_options = {
            "name": ["full_name", "person_name", "display_name", "user_name"],
            "id": ["record_id", "row_id", "entry_id", "item_id"],
            "value": ["amount", "score", "total", "quantity"],
        }
        renames = {}
        for col, options in rename_options.items():
            renames[col] = self._rng.choice(options)
        return renames

    def generate_extra_columns(self) -> list[str]:
        """Extra columns that should be dropped."""
        options = ["region", "_timestamp", "source", "_metadata", "notes",
                   "created_at", "updated_at", "status", "priority"]
        n = self._rng.randint(1, 3)
        return self._rng.sample(options, n)


def deterministic_hash(seed: int, salt: str = "") -> str:
    """Generate a deterministic hex hash from seed + salt."""
    data = f"{seed}:{salt}".encode()
    return hashlib.sha256(data).hexdigest()
