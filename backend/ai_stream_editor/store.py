import json
from contextlib import contextmanager
from pathlib import Path
import sqlite3


class Store:
    def __init__(self, data_dir: Path):
        data_dir.mkdir(parents=True, exist_ok=True)
        self.path = data_dir / "projects.sqlite3"
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS records (kind TEXT, id TEXT, data TEXT NOT NULL, PRIMARY KEY(kind, id))")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        try:
            with db:
                yield db
        finally:
            db.close()

    def get(self, kind: str, record_id: str) -> dict | None:
        with self.connect() as db:
            row = db.execute("SELECT data FROM records WHERE kind=? AND id=?", (kind, record_id)).fetchone()
        return json.loads(row[0]) if row else None

    def all(self, kind: str) -> list[dict]:
        with self.connect() as db:
            rows = db.execute("SELECT data FROM records WHERE kind=? ORDER BY rowid", (kind,)).fetchall()
        return [json.loads(row[0]) for row in rows]

    def put(self, kind: str, value: dict):
        self.put_many([(kind, value)])

    def project_summaries(self) -> list[dict]:
        with self.connect() as db:
            rows = db.execute("SELECT json_remove(data, '$.transcript') FROM records WHERE kind='project' ORDER BY rowid DESC").fetchall()
        return [json.loads(row[0]) for row in rows]

    def related(self, kind: str, project_id: str) -> list[dict]:
        with self.connect() as db:
            rows = db.execute("SELECT data FROM records WHERE kind=? AND json_extract(data, '$.project_id')=? ORDER BY rowid DESC", (kind, project_id)).fetchall()
        return [json.loads(row[0]) for row in rows]

    def count_related(self, kind: str, project_id: str) -> int:
        with self.connect() as db:
            return db.execute("SELECT count(*) FROM records WHERE kind=? AND json_extract(data, '$.project_id')=?", (kind, project_id)).fetchone()[0]

    def latest_job(self, project_id: str, kind: str) -> dict | None:
        with self.connect() as db:
            row = db.execute("SELECT data FROM records WHERE kind='job' AND json_extract(data, '$.project_id')=? AND json_extract(data, '$.kind')=? ORDER BY rowid DESC LIMIT 1", (project_id, kind)).fetchone()
        return json.loads(row[0]) if row else None

    def put_many(self, records: list[tuple[str, dict]], *, remove_pending_export: str | None = None):
        rows = [(kind, value["id"], json.dumps(value, ensure_ascii=False, allow_nan=False)) for kind, value in records]
        with self.connect() as db:
            db.executemany("INSERT INTO records(kind,id,data) VALUES (?,?,?) ON CONFLICT(kind,id) DO UPDATE SET data=excluded.data", rows)
            if remove_pending_export is not None:
                db.execute("DELETE FROM records WHERE kind='export_pending' AND id=?", (remove_pending_export,))

    def gallery_page(self, review_status: str, cursor: int | None, limit: int):
        with self.connect() as db:
            rows = db.execute("""
                SELECT c.rowid, c.data,
                       json_extract(p.data, '$.source'),
                       coalesce(json_extract(p.data, '$.analyzed_at'), json_extract(p.data, '$.created_at'))
                FROM records c JOIN records p ON p.kind='project'
                     AND p.id=json_extract(c.data, '$.project_id')
                WHERE c.kind='clip' AND (?='all' OR json_extract(c.data, '$.review_status')=?)
                  AND (? IS NULL OR c.rowid < ?)
                  AND json_extract(c.data, '$.preview_revision')=json_extract(c.data, '$.revision')
                  AND json_extract(c.data, '$.preview_file') IS NOT NULL
                ORDER BY c.rowid DESC LIMIT ?
                """, (review_status, review_status, cursor, cursor, limit)).fetchall()
        return [(row[0], json.loads(row[1]), json.loads(row[2]) if row[2] else None, row[3]) for row in rows]

    def gallery_updated_at(self):
        with self.connect() as db:
            return db.execute("""SELECT max(json_extract(data, '$.updated_at')) FROM records
                WHERE kind='job' AND json_extract(data, '$.kind')='render'
                  AND json_extract(data, '$.status')='succeeded'""").fetchone()[0]
