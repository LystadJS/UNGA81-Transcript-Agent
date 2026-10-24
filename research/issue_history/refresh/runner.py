"""Bounded incremental refresh with durable checkpoints and conservative publication."""
import datetime as dt
import json
from pathlib import Path
from ..ingest.runner import run_checkpointed
from ..store import canonical_bytes


def transcript_sink(store, body, access="private", extract=None):
    """Bridge verified normalized records to canonical source revisions.

    Optional extraction must return store-schema observations; the bridge stamps
    the canonical revision instead of trusting an adapter-specific digest.
    """
    def persist(row):
        source_id = row["source_id"]
        revision = store.upsert_source({"id": source_id, "published_date": row["date"], "body": body,
            "family": "un_statement", "url": row["source_url"], "content_hash": row["text_sha256"],
            "access": access, "countries": [row["country"]]})
        for observation in extract(row) if extract else []:
            store.put_observation({**observation, "source_id": source_id, "source_revision": revision})
    return persist


def refresh(*, rows, adapter, persist, store, checkpoint, bundle_directory,
            snapshot_id, health_path, limit=100, watermark=None):
    """Run one batch; publish only a complete, unquarantined input snapshot.

    The caller provides an approved source snapshot and source-side watermark.
    A successful local job alone does not establish remote source freshness.
    """
    if watermark is not None:
        dt.date.fromisoformat(watermark)
    health_path = Path(health_path)
    health_path.parent.mkdir(parents=True, exist_ok=True)
    prior = json.loads(health_path.read_text(encoding="utf-8")) if health_path.exists() else {}
    health = {"schema": "un.issue-history.refresh-health.v1", "snapshot_id": snapshot_id,
              "last_published_snapshot": prior.get("last_published_snapshot"),
              "source_watermark": prior.get("source_watermark"), "status": "running"}
    try:
        state = run_checkpointed(rows, adapter, persist, checkpoint, limit=limit)
        health["coverage"] = state["coverage"]
        if not state["complete"]:
            health["status"] = "incomplete"
        elif state["quarantine"]:
            health["status"] = "quarantined"
        else:
            counts = state["coverage"]
            store.export_bundle(bundle_directory, snapshot_id, {"status": "complete_input_snapshot",
                "expected": counts["expected"], "retrieved": counts["processed"], "verified": counts["accepted"], "unavailable": 0, "excluded": 0}, partition=True)
            health.update(status="published", last_published_snapshot=snapshot_id, source_watermark=watermark)
        store._atomic_write(health_path, canonical_bytes(health))
        return health
    except Exception:
        # Source text and exception messages cannot leak into public health state.
        health["status"] = "failed"
        store._atomic_write(health_path, canonical_bytes(health))
        raise


def refresh_private_actions(**options):
    """Refresh selected voting actions privately; never ingest or export bundles.

    Completed source ingestion is a prerequisite. The accepted cache verifies
    its own dependencies; this lane advances only a separate private pointer.
    """
    from .sc_action_refresh import refresh_selected_actions
    return refresh_selected_actions(**options)
