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
    "src/security.py",
    "templates/admin_archive.html",
    "templates/admin_create_regulation.html",
    "templates/admin_create_task.html",
    "templates/admin_regulation_list.html",
    "templates/admin_task_details.html",
    "templates/admin_task_list.html",
    "templates/admin_train_details.html",
    "templates/admin_upcoming_repairs.html",
    "templates/base.html",
    "templates/custom_create.html",
    "templates/custom_details.html",
    "templates/custom_edit.html",
    "templates/custom_list.html",
    "templates/dashboard.html",
    "templates/login.html",
    "templates/translate_script.html",
    "templates/workspace.html",
    ]


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