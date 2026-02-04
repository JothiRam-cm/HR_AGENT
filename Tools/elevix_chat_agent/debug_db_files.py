
from src.database import DatabaseManager

try:
    db = DatabaseManager()
    files = db.get_all_files()
    print(f"Files in DB: {len(files)}")
    for f in files:
        print(f"- {f['filename']} ({f['size_bytes']} bytes)")
except Exception as e:
    print(f"Error: {e}")
