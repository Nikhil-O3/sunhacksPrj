import os

from radon.complexity import cc_visit
from radon.metrics import mi_visit
from radon.raw import analyze


def _empty_metrics() -> dict:
    return {
        "complexity": 0,
        "maintainability": 0.0,
        "loc": 0,
        "sloc": 0,
        "radon_focus": [],
        "radon_focus_summary": "Radon did not find Python functions/classes to score.",
    }


def _summarize_focus(blocks: list[dict]) -> str:
    if not blocks:
        return "Radon did not find Python functions/classes to score."

    ranges = []
    for block in blocks[:5]:
        start_line = block["start_line"]
        end_line = block["end_line"]
        if start_line == end_line:
            location = f"line {start_line}"
        else:
            location = f"lines {start_line}-{end_line}"
        ranges.append(f"{block['name']} ({location}, complexity {block['complexity']})")

    if len(blocks) > 5:
        ranges.append(f"{len(blocks) - 5} more block(s)")
    return "; ".join(ranges)


def compute_code_metrics_detail(file_path: str) -> dict:
    if not os.path.isfile(file_path):
        return _empty_metrics()
    if not file_path.endswith(".py"):
        return _empty_metrics()

    try:
        with open(file_path, "r", encoding="utf-8") as handle:
            source = handle.read()

        blocks = []
        for block in cc_visit(source):
            block_type = "class" if getattr(block, "letter", "") == "C" else "function"
            blocks.append(
                {
                    "name": getattr(block, "fullname", None) or getattr(block, "name", "unknown"),
                    "type": block_type,
                    "start_line": getattr(block, "lineno", 0) or 0,
                    "end_line": getattr(block, "endline", None) or getattr(block, "lineno", 0) or 0,
                    "complexity": getattr(block, "complexity", 0) or 0,
                }
            )

        complexity = sum(block["complexity"] for block in blocks)
        maintainability = mi_visit(source, True)
        if maintainability is None:
            maintainability = 0.0

        raw_metrics = analyze(source)
        return {
            "complexity": complexity,
            "maintainability": round(maintainability, 1),
            "loc": raw_metrics.loc,
            "sloc": raw_metrics.sloc,
            "radon_focus": blocks,
            "radon_focus_summary": _summarize_focus(blocks),
        }
    except Exception:
        return _empty_metrics()


def compute_code_metrics(file_path: str) -> tuple[int, float]:
    metrics = compute_code_metrics_detail(file_path)
    return metrics["complexity"], metrics["maintainability"]
