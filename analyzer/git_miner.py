from collections import defaultdict
import os

from pydriller import Repository


def analyze_languages(repo_path: str) -> dict:
    """Analyze programming languages used in the repository."""
    language_stats = defaultdict(int)
    total_lines = 0

    # Language detection based on file extensions
    language_map = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.jsx': 'React',
        '.tsx': 'React TypeScript',
        '.java': 'Java',
        '.cpp': 'C++',
        '.c': 'C',
        '.cs': 'C#',
        '.php': 'PHP',
        '.rb': 'Ruby',
        '.go': 'Go',
        '.rs': 'Rust',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.html': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.sass': 'Sass',
        '.less': 'Less',
        '.sql': 'SQL',
        '.sh': 'Shell',
        '.bash': 'Bash',
        '.zsh': 'Zsh',
        '.yml': 'YAML',
        '.yaml': 'YAML',
        '.json': 'JSON',
        '.xml': 'XML',
        '.md': 'Markdown',
        '.txt': 'Text',
        '.dockerfile': 'Docker',
        'Dockerfile': 'Docker',
        '.gitignore': 'Git',
        '.env': 'Environment',
    }

    try:
        for root, dirs, files in os.walk(repo_path):
            # Skip .git directory and common non-code directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv', 'venv', 'env']]

            for file in files:
                file_path = os.path.join(root, file)
                _, ext = os.path.splitext(file.lower())

                # Special cases
                if file.lower() in ['dockerfile', '.dockerfile']:
                    ext = 'dockerfile'
                elif file.lower().startswith('dockerfile'):
                    ext = 'dockerfile'

                language = language_map.get(ext, language_map.get(file.lower(), 'Other'))

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        line_count = len(lines)
                        language_stats[language] += line_count
                        total_lines += line_count
                except:
                    # If we can't read the file, just count it as 1 line
                    language_stats[language] += 1
                    total_lines += 1

        # Convert to percentages
        language_percentages = {}
        for lang, lines in language_stats.items():
            if total_lines > 0:
                language_percentages[lang] = round((lines / total_lines) * 100, 1)
            else:
                language_percentages[lang] = 0.0

        return {
            'languages': dict(sorted(language_percentages.items(), key=lambda x: x[1], reverse=True)),
            'total_lines': total_lines
        }
    except Exception:
        return {'languages': {}, 'total_lines': 0}


def analyze_git_history(repo_path: str) -> list[dict]:
    file_stats: dict[str, dict] = {}

    try:
        for commit in Repository(repo_path).traverse_commits():
            author_key = commit.author.email or commit.author.name or "unknown"
            try:
                modifications = commit.modified_files
            except Exception:
                continue

            # Check if commit message indicates bug fix
            commit_msg = (commit.msg or "").lower()
            is_bug_fix = any(keyword in commit_msg for keyword in [
                "fix", "bug", "issue", "error", "defect", "patch", "hotfix",
                "resolve", "correct", "repair", "debug"
            ])

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
                        "bug_fixes": 0,
                        "total_changes": 0,
                    },
                )
                stat["commits"] += 1
                churn_added = getattr(mod, "added_lines", None)
                churn_removed = getattr(mod, "deleted_lines", None)
                if churn_added is None or churn_removed is None:
                    churn_added = getattr(mod, "added", 0) or 0
                    churn_removed = getattr(mod, "removed", 0) or 0
                stat["churn"] += churn_added + churn_removed
                stat["contributors"].add(author_key)
                stat["total_changes"] += churn_added + churn_removed
                if is_bug_fix:
                    stat["bug_fixes"] += 1
                if stat["last_commit_date"] is None or commit.committer_date > stat["last_commit_date"]:
                    stat["last_commit_date"] = commit.committer_date

        rows = []
        for stat in file_stats.values():
            # Calculate bug resolution rate (bugs fixed vs total changes)
            bug_resolution_rate = 0.0
            if stat["total_changes"] > 0:
                bug_resolution_rate = min(1.0, stat["bug_fixes"] / max(1, stat["total_changes"] / 100))  # Normalize

            rows.append(
                {
                    "file_path": stat["file_path"],
                    "commits": stat["commits"],
                    "churn": stat["churn"],
                    "contributors": len(stat["contributors"]),
                    "bug_fixes": stat["bug_fixes"],
                    "bug_resolution_rate": round(bug_resolution_rate, 3),
                    "last_commit_date": stat["last_commit_date"].isoformat()
                    if stat["last_commit_date"]
                    else None,
                }
            )
        return rows
    except Exception:
        return []
