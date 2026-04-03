from pathlib import Path

from app.config import load_topics


def main() -> None:
    topics = load_topics()
    print(f"Loaded {len(topics)} topics from config.")
    for t in topics:
        print(f"- {t.slug}: {t.label} ({', '.join(t.query_keywords)})")
    print(f"Path: {Path('config/topics.yaml').resolve()}")


if __name__ == "__main__":
    main()
