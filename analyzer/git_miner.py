from collections import defaultdict

from pydriller import Repository


def analyze_git_history(repo_path: str) -> list[dict]:
    file_stats: dict[str, dict] = {}

    try:
        for commit in Repository(repo_path).traverse_commits():
            author_key = commit.author.email or commit.author.name or "unknown"
            try:
                modifications = commit.modified_files
            except Exception:
                continue

            for mod in modifications:
                file_path = getattr(mod, "new_path", None) or getattr(mod, "old_path", None)
                if not file_path:
                    continue

                stat = file_stats.setdefault(
                    file_path,
                    {
                        "file_path": file_path,
                        "commits": 0,
                        "churn": 0,
                        "contributors": set(),
                        "last_commit_date": None,
                    },
                )
                stat["commits"] += 1
                stat["churn"] += (getattr(mod, "added", 0) or 0) + (getattr(mod, "removed", 0) or 0)
                stat["contributors"].add(author_key)
                if stat["last_commit_date"] is None or commit.committer_date > stat["last_commit_date"]:
                    stat["last_commit_date"] = commit.committer_date

        rows = []
        for stat in file_stats.values():
            rows.append(
                {
                    "file_path": stat["file_path"],
                    "commits": stat["commits"],
                    "churn": stat["churn"],
                    "contributors": len(stat["contributors"]),
                    "last_commit_date": stat["last_commit_date"].isoformat()
                    if stat["last_commit_date"]
                    else None,
                }
            )
        return rows
    except Exception:
        return []
