import os

from radon.complexity import cc_visit
from radon.metrics import mi_visit


def compute_code_metrics(file_path: str) -> tuple[int, float]:
    if not os.path.isfile(file_path):
        return 0, 0.0
    if not file_path.endswith(".py"):
        return 0, 0.0

    try:
        with open(file_path, "r", encoding="utf-8") as handle:
            source = handle.read()

        complexity = sum(block.complexity for block in cc_visit(source))
        maintainability = mi_visit(source, True)
        if maintainability is None:
            maintainability = 0.0
        return complexity, round(maintainability, 1)
    except Exception:
        return 0, 0.0
