"""
Pure‑python module that *another* piece of python code can import.
Demonstrates “passing information from one python code to another”.
"""

import random
from typing import List, Dict

def _rand_sign() -> int:          # –1 or +1
    return 1 if random.random() < .5 else -1

def make_cube(i: int) -> Dict:
    """Return a dict Three.js can turn into one cube."""
    return {
        "id": f"cube-{i}",
        "size": random.uniform(0.5, 2.0),
        "x": _rand_sign() * random.uniform(0, 5),
        "y": _rand_sign() * random.uniform(0, 5),
        "z": _rand_sign() * random.uniform(0, 5),
        "rotation_speed": random.uniform(0.001, 0.01),
    }

def build_scene_data(n: int = 10) -> List[Dict]:
    """Public API for the rest of the backend."""
    return [make_cube(i) for i in range(n)]
