import os
from datetime import datetime, timedelta
from uuid import UUID

import requests
from fastapi import APIRouter, HTTPException
from app.database import get_connection

router = APIRouter(prefix="/events", tags=["recommend"])

SCHEDULER_URL = os.getenv("SCHEDULER_URL", "http://localhost:8080")
SLOT_MINUTES = 60  # ukuran slot waktu, selaras dengan durasi acara default 1 jam


def _slots_for_range(start: datetime, end: datetime):
    """Pecah satu rentang availability jadi slot per jam."""
    slots = []
    cur = start.replace(minute=0, second=0, microsecond=0)
    if cur < start:
        cur += timedelta(hours=1)
    while cur + timedelta(minutes=SLOT_MINUTES) <= end:
        slots.append(cur)
        cur += timedelta(minutes=SLOT_MINUTES)
    return slots


@router.post("/{event_id}/recommend-times")
def recommend_times(event_id: UUID):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT event_id FROM events WHERE event_id = %s", (str(event_id),))
        if cur.fetchone() is None:
            raise HTTPException(status_code=404, detail="Acara tidak ditemukan")

        cur.execute(
            "SELECT user_id, start_time, end_time, status "
            "FROM availability WHERE event_id = %s",
            (str(event_id),),
        )
        rows = cur.fetchall()
        if not rows:
            raise HTTPException(
                status_code=400,
                detail="Belum ada data availability untuk acara ini",
            )

        # Susun slots per user: {user_id: {"2026-10-10T09:00": "available", ...}}
        participants_map: dict[str, dict[str, str]] = {}
        for user_id, start_time, end_time, status in rows:
            uid = str(user_id)
            participants_map.setdefault(uid, {})
            for slot_start in _slots_for_range(start_time, end_time):
                label = slot_start.strftime("%Y-%m-%dT%H:%M")
                # Kalau ada slot yang tumpang tindih, busy menang (paling konservatif)
                existing = participants_map[uid].get(label)
                if existing != "busy":
                    participants_map[uid][label] = status

        participants = [
            {"name": uid, "slots": slots} for uid, slots in participants_map.items()
        ]

        payload = {"participants": participants}
        try:
            resp = requests.post(f"{SCHEDULER_URL}/recommend", json=payload, timeout=5)
            resp.raise_for_status()
        except requests.RequestException as error:
            raise HTTPException(
                status_code=502,
                detail=f"Gagal menghubungi scheduler: {error}",
            )

        result = resp.json()
        recommendations = result.get("recommendations", [])

        saved = []
        for rec in recommendations[:3]:  # simpan 3 kandidat teratas
            slot_start = datetime.strptime(rec["slot"], "%Y-%m-%dT%H:%M")
            slot_end = slot_start + timedelta(minutes=SLOT_MINUTES)
            cur.execute(
                """
                INSERT INTO time_candidates (event_id, start_time, end_time, score, status)
                VALUES (%s, %s, %s, %s, 'proposed')
                RETURNING candidate_id, start_time, end_time, score, status
                """,
                (str(event_id), slot_start, slot_end, rec["score"]),
            )
            row = cur.fetchone()
            saved.append(
                {
                    "candidate_id": str(row[0]),
                    "start_time": row[1],
                    "end_time": row[2],
                    "score": float(row[3]),
                    "status": row[4],
                }
            )
        conn.commit()

        return {
            "event_id": str(event_id),
            "model_version": result.get("model_version"),
            "participant_count": result.get("participant_count"),
            "candidates_saved": saved,
        }
    finally:
        cur.close()
        conn.close()
