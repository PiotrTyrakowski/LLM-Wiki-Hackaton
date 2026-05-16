"""First-class Redis usage (on top of cognee's session memory):
  - Streams: append-only audit log of agent events (XADD/XRANGE).
  - Pub/Sub: live channel for the viz to subscribe to.
  - Vector index: source-clip embeddings for semantic clip matching.

Keep this module small. Cognee owns session memory; this owns Redis-native features.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import redis

from .config import REDIS_PUBSUB_CHANNEL, REDIS_STREAM_EVENTS, REDIS_URL, REDIS_VECTOR_INDEX


def client() -> redis.Redis:
    return redis.Redis.from_url(REDIS_URL, decode_responses=False)


def publish_event(kind: str, payload: dict[str, Any]) -> None:
    """Emit one event to both a stream (durable) and a pubsub channel (live)."""
    r = client()
    body = {"kind": kind, **{k: json.dumps(v) if not isinstance(v, (str, int, float, bool, bytes)) else v for k, v in payload.items()}}
    try:
        r.xadd(REDIS_STREAM_EVENTS, body, maxlen=10_000, approximate=True)
    except Exception as exc:  # pragma: no cover
        print(f"[redis] xadd skipped: {exc}")
    try:
        r.publish(REDIS_PUBSUB_CHANNEL, json.dumps({"kind": kind, **payload}))
    except Exception:
        pass


def read_recent_events(count: int = 50) -> list[dict[str, str]]:
    r = client()
    entries = r.xrevrange(REDIS_STREAM_EVENTS, count=count)
    out = []
    for entry_id, fields in entries:
        decoded = {k.decode(): (v.decode() if isinstance(v, bytes) else v) for k, v in fields.items()}
        decoded["_id"] = entry_id.decode() if isinstance(entry_id, bytes) else entry_id
        out.append(decoded)
    return out


def stream_subscribe():
    """Generator yielding pubsub messages on REDIS_PUBSUB_CHANNEL."""
    r = client()
    sub = r.pubsub()
    sub.subscribe(REDIS_PUBSUB_CHANNEL)
    for msg in sub.listen():
        if msg["type"] == "message":
            data = msg["data"]
            if isinstance(data, bytes):
                data = data.decode()
            try:
                yield json.loads(data)
            except Exception:
                yield {"kind": "raw", "data": data}


# ---------- Vector index (RediSearch) ----------

def _index_exists(r: redis.Redis, index: str) -> bool:
    try:
        r.execute_command("FT.INFO", index)
        return True
    except Exception:
        return False


def ensure_clip_index(dim: int = 1536) -> None:
    """Idempotently create a flat L2 HNSW vector index for source clips."""
    r = client()
    if _index_exists(r, REDIS_VECTOR_INDEX):
        return
    try:
        r.execute_command(
            "FT.CREATE", REDIS_VECTOR_INDEX,
            "ON", "HASH",
            "PREFIX", "1", "clip:",
            "SCHEMA",
            "name", "TEXT",
            "kind", "TAG",
            "duration", "NUMERIC",
            "description", "TEXT",
            "embedding", "VECTOR", "HNSW", "6",
            "TYPE", "FLOAT32",
            "DIM", str(dim),
            "DISTANCE_METRIC", "COSINE",
        )
    except Exception as exc:
        print(f"[redis] FT.CREATE skipped: {exc}")


def upsert_clip(clip_id: str, name: str, kind: str, duration: float, description: str, embedding: np.ndarray) -> None:
    r = client()
    vec_bytes = np.asarray(embedding, dtype=np.float32).tobytes()
    r.hset(
        f"clip:{clip_id}",
        mapping={
            "name": name,
            "kind": kind,
            "duration": float(duration),
            "description": description,
            "embedding": vec_bytes,
        },
    )


def search_clips(query_vec: np.ndarray, k: int = 5) -> list[dict[str, Any]]:
    """KNN search against the clip vector index. Returns top-k clip metadata."""
    r = client()
    if not _index_exists(r, REDIS_VECTOR_INDEX):
        return []
    q = f"*=>[KNN {k} @embedding $vec AS score]"
    vec = np.asarray(query_vec, dtype=np.float32).tobytes()
    try:
        res = r.execute_command(
            "FT.SEARCH", REDIS_VECTOR_INDEX, q,
            "RETURN", "4", "name", "kind", "duration", "description",
            "SORTBY", "score", "ASC",
            "DIALECT", "2",
            "PARAMS", "2", "vec", vec,
        )
    except Exception as exc:
        print(f"[redis] FT.SEARCH error: {exc}")
        return []
    # FT.SEARCH returns: [total, key1, [field1, value1, ...], key2, [...], ...]
    out = []
    if not res or len(res) < 2:
        return out
    it = iter(res[1:])
    for key in it:
        fields = next(it, [])
        d: dict[str, Any] = {"key": key.decode() if isinstance(key, bytes) else key}
        for i in range(0, len(fields), 2):
            k_ = fields[i].decode() if isinstance(fields[i], bytes) else fields[i]
            v_ = fields[i + 1]
            if isinstance(v_, bytes):
                try:
                    v_ = v_.decode()
                except Exception:
                    pass
            d[k_] = v_
        out.append(d)
    return out
