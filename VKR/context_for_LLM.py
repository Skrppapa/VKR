from pathlib import Path

# Папки и файлы, которые нужно собрать
TARGET_DIRS = [
    "src/api",
    "src/models",
    "src/repositories",
    "src/schemas",
    "src/services",
    "src/sql_admin",
    "src/utils",
    "src/config.py",
    "src/database.py",
    "src/main.py",
    "src/security.py"]
OUTPUT_FILE = "llm_context.md"


def gather_context():
    with open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
        for dir_name in TARGET_DIRS:
            path = Path(dir_name)
            if not path.exists():
                continue

            for file_path in path.rglob("*.py"):
                outfile.write(f"\n\n### File: {file_path}\n")
                outfile.write("```python\n")
                with open(file_path, "r", encoding="utf-8") as f:
                    outfile.write(f.read())
                outfile.write("\n```\n")

    print(f"Контекст успешно собран в {OUTPUT_FILE}")


if __name__ == "__main__":
    gather_context()