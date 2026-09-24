from fastapi import APIRouter, HTTPException
from uuid import UUID
from app.database import get_connection

router = APIRouter(prefix="/events", tags=["status"])

# Peserta acara = anggota yang sudah joined + organizer acara itu sendiri
PARTICIPANTS_CTE = """
    WITH participants AS (
        SELECT user_id FROM event_members
        WHERE event_id = %(eid)s AND member_status = 'joined'
        UNION
        SELECT organizer_id FROM events WHERE event_id = %(eid)s
    )
"""


@router.post("/{event_id}/evaluate-cancel")
def evaluate_cancel(event_id: UUID):
    conn = get_connection()
    cur = conn.cursor()
    params = {"eid": str(event_id)}
    try:
        cur.execute("SELECT status FROM events WHERE event_id = %(eid)s", params)
        event = cur.fetchone()
        if event is None:
            raise HTTPException(status_code=404, detail="Acara tidak ditemukan")
        current_status = event[0]

        cur.execute(PARTICIPANTS_CTE + "SELECT COUNT(*) FROM participants", params)
        total_members = cur.fetchone()[0]

        # Ambil pilihan terakhir tiap peserta
        cur.execute(
            PARTICIPANTS_CTE
            + """
            SELECT COUNT(*) FROM (
                SELECT DISTINCT ON (cr.user_id) cr.is_cancel
                FROM cancel_requests cr
                WHERE cr.event_id = %(eid)s
                  AND cr.user_id IN (SELECT user_id FROM participants)
                ORDER BY cr.user_id, cr.created_at DESC
            ) latest
            WHERE latest.is_cancel
            """,
            params,
        )
        cancel_count = cur.fetchone()[0]

        # Acara dibatalkan hanya jika seluruh peserta memilih cancel
        all_cancel = total_members > 0 and cancel_count == total_members

        new_status = current_status
        if all_cancel and current_status in ("draft", "active"):
            cur.execute(
                "UPDATE events SET status = 'cancelled' "
                "WHERE event_id = %(eid)s RETURNING status",
                params,
            )
            new_status = cur.fetchone()[0]
            conn.commit()

        # Hanya agregat yang dikembalikan, identitas pemilih tidak ditampilkan
        return {
            "event_id": str(event_id),
            "total_members": total_members,
            "cancel_count": cancel_count,
            "status": new_status,
        }
    finally:
        cur.close()
        conn.close()
