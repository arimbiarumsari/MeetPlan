from fastapi import APIRouter, HTTPException
from app.database import get_connection
from app.models.availability import AvailabilityCreate, AvailabilityOut
from uuid import UUID


router = APIRouter(prefix="/availability", tags=["availability"])


@router.post("/", response_model=AvailabilityOut)
def create_availability(availability: AvailabilityCreate):
    if availability.end_time <= availability.start_time:
        raise HTTPException(
            status_code=400,
            detail="End time must be after start time"
        )

    if availability.status not in ["busy", "tentative"]:
        raise HTTPException(
            status_code=400,
            detail="Status must be busy or tentative"
        )

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO availability
            (event_id, user_id, start_time, end_time, status)
        VALUES
            (%s, %s, %s, %s, %s)
        RETURNING
            availability_id, event_id, user_id,
            start_time, end_time, status
        """,
        (
            str(availability.event_id),
            str(availability.user_id),
            availability.start_time,
            availability.end_time,
            availability.status
        )
    )

    row = cur.fetchone()

    conn.commit()
    cur.close()
    conn.close()

    return availability_row_to_dict(row)


@router.get("/{event_id}", response_model=list[AvailabilityOut])
def get_availability(event_id: UUID):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            availability_id, event_id, user_id,
            start_time, end_time, status
        FROM availability
        WHERE event_id = %s
        ORDER BY start_time
        """,
        (str(event_id),)
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [availability_row_to_dict(row) for row in rows]


def availability_row_to_dict(row):
    return {
        "availability_id": row[0],
        "event_id": row[1],
        "user_id": row[2],
        "start_time": row[3],
        "end_time": row[4],
        "status": row[5],
    }