"""Versioned evidence ingestion for a scoped consultancy study, using local SQLite."""

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from enerqit.quality import validate_frame


class StudyStore:
    """Store latest observations, immutable batch history and analysis snapshots.

    A repeated identical batch is a no-op. Newer ingestion replaces conflicting
    timestamps for one asset; original batches remain in the audit trail. A
    reference analysis cannot be overwritten by subsequent daily evidence.
    This is a local research store, not a multi-user production service.
    """

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as con:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS batches (
                    asset TEXT, digest TEXT, ingested_at TEXT, payload TEXT,
                    PRIMARY KEY(asset, digest));
                CREATE TABLE IF NOT EXISTS observations (
                    asset TEXT, timestamp TEXT, payload TEXT, batch TEXT,
                    PRIMARY KEY(asset, timestamp));
                CREATE TABLE IF NOT EXISTS analyses (
                    asset TEXT, version TEXT, created_at TEXT, data_digest TEXT,
                    result TEXT, is_reference INTEGER,
                    PRIMARY KEY(asset, version));
                CREATE UNIQUE INDEX IF NOT EXISTS one_reference
                    ON analyses(asset) WHERE is_reference=1;
            """)

    def _connection(self):
        return sqlite3.connect(self.path)

    def ingest(self, asset, frame):
        """Atomically upsert a batch; return idempotency and replacement counts."""
        validate_frame(frame, frame.columns)
        if not isinstance(asset, str) or not asset.strip() or not len(frame.columns):
            raise ValueError("nonempty asset and numeric observation columns required")
        canonical = frame.copy().sort_index(axis=1)
        canonical.index = canonical.index.tz_convert("UTC")
        records = [
            {"timestamp": ts.isoformat(), "values": {str(k): float(v) for k, v in row.items()}}
            for ts, row in canonical.iterrows()
        ]
        payload = json.dumps(records, sort_keys=True, allow_nan=False)
        digest = hashlib.sha256(payload.encode()).hexdigest()
        inserted = replaced = 0
        with self._connection() as con:
            if con.execute(
                "SELECT 1 FROM batches WHERE asset=? AND digest=?", (asset, digest)
            ).fetchone():
                return {"digest": digest, "inserted": 0, "replaced": 0, "duplicate": True}
            # A fixed schema avoids silently erasing old channels in partial uploads.
            existing = con.execute(
                "SELECT payload FROM observations WHERE asset=? LIMIT 1", (asset,)
            ).fetchone()
            if existing and set(json.loads(existing[0])) != set(canonical.columns):
                raise ValueError("batch schema differs from stored asset channels")
            con.execute(
                "INSERT INTO batches VALUES (?,?,?,?)",
                (asset, digest, datetime.now(timezone.utc).isoformat(), payload),
            )
            for record in records:
                ts = record["timestamp"]
                old = con.execute(
                    "SELECT payload FROM observations WHERE asset=? AND timestamp=?", (asset, ts)
                ).fetchone()
                value = json.dumps(record["values"], sort_keys=True)
                inserted += old is None
                replaced += old is not None and old[0] != value
                con.execute(
                    "INSERT OR REPLACE INTO observations VALUES (?,?,?,?)",
                    (asset, ts, value, digest),
                )
        return {
            "digest": digest,
            "inserted": int(inserted),
            "replaced": int(replaced),
            "duplicate": False,
        }

    def frame(self, asset):
        """Return current evidence for one asset, ordered in UTC."""
        with self._connection() as con:
            rows = con.execute(
                "SELECT timestamp,payload FROM observations WHERE asset=? ORDER BY timestamp",
                (asset,),
            ).fetchall()
        if not rows:
            raise KeyError(asset)
        return pd.DataFrame(
            [json.loads(r[1]) for r in rows],
            index=pd.DatetimeIndex([r[0] for r in rows], name="timestamp"),
        )

    def snapshot(self, asset, version, result, *, reference=False):
        """Append an immutable result linked to the current evidence digest.

        The caller must ensure the result was fitted to that evidence. Include
        fit settings and model versions in result.provenance for reproducibility.
        Duplicate versions/reference designations raise sqlite3.IntegrityError.
        """
        frame = self.frame(asset)
        digest = hashlib.sha256(frame.to_csv().encode()).hexdigest()
        payload = (
            result.to_json() if hasattr(result, "to_json") else json.dumps(result, allow_nan=False)
        )
        with self._connection() as con:
            con.execute(
                "INSERT INTO analyses VALUES (?,?,?,?,?,?)",
                (
                    asset,
                    version,
                    datetime.now(timezone.utc).isoformat(),
                    digest,
                    payload,
                    int(reference),
                ),
            )
        return digest

    def analyses(self, asset):
        """Return analysis versions with immutable evidence hashes and results."""
        with self._connection() as con:
            rows = con.execute(
                "SELECT version,data_digest,result,is_reference FROM analyses WHERE asset=? ORDER BY created_at",
                (asset,),
            ).fetchall()
        return [
            {"version": v, "data_digest": d, "result": json.loads(r), "reference": bool(ref)}
            for v, d, r, ref in rows
        ]
