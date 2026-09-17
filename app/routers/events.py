from fastapi import APIRouter, HTTPException
from app.database import get_connection
from app.models.event import EventCreate, EventUpdate, EventOut
from uuid import UUID

router = APIRouter(prefix="/events", tags=["events"])

@router.post("/", response_model=EventOut)
def create_event(event: EventCreate):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO events (organizer_id, event_name, description)
        VALUES (%s, %s, %s)
        RETURNING event_id, organizer_id, event_name, description, duration,
                  final_time, final_location, final_activity, status, created_at
        """,
        (str(event.organizer_id), event.event_name, event.description)
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return event_row_to_dict(row)


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: UUID):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT event_id, organizer_id, event_name, description, duration,
               final_time, final_location, final_activity, status, created_at
        FROM events WHERE event_id = %s
        """,
        (str(event_id),)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event_row_to_dict(row)

@router.patch("/{event_id}", response_model=EventOut)
def update_event(event_id: UUID, event: EventUpdate):
    conn = get_connection()
    cur = conn.cursor()

    fields = event.model_dump(exclude_unset=True)
    if not fields:
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="No fields to update")

    set_clause = ", ".join(f"{key} = %s" for key in fields)
    values = list(fields.values()) + [str(event_id)]

    cur.execute(
        f"""
        UPDATE events SET {set_clause}
        WHERE event_id = %s
        RETURNING event_id, organizer_id, event_name, description, duration,
                  final_time, final_location, final_activity, status, created_at
        """,
        values
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event_row_to_dict(row)


@router.delete("/{event_id}")
def delete_event(event_id: UUID):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM events WHERE event_id = %s RETURNING event_id", (str(event_id),))
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"message": "Event deleted", "event_id": event_id}

def event_row_to_dict(row):
    return {
        "event_id": row[0],
        "organizer_id": row[1],
        "event_name": row[2],
        "description": row[3],
        "duration": row[4],
        "final_time": row[5],
        "final_location": row[6],
        "final_activity": row[7],
        "status": row[8],
        "created_at": row[9],
    }