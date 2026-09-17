from fastapi import APIRouter, HTTPException
from app.database import get_connection
from app.models.member import MemberInvite, MemberStatusUpdate, MemberOut
from uuid import UUID
from typing import List

router = APIRouter(prefix="/events", tags=["members"])


@router.post("/{event_id}/invite", response_model=MemberOut)
def invite_member(event_id: UUID, invite: MemberInvite):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO event_members (event_id, user_id)
        VALUES (%s, %s)
        RETURNING event_id, user_id, member_status, joined_at
        """,
        (str(event_id), str(invite.user_id))
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return member_row_to_dict(row)


@router.get("/{event_id}/members", response_model=List[MemberOut])
def list_members(event_id: UUID):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT event_id, user_id, member_status, joined_at
        FROM event_members WHERE event_id = %s
        """,
        (str(event_id),)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [member_row_to_dict(row) for row in rows]


@router.patch("/{event_id}/members/{user_id}", response_model=MemberOut)
def update_member_status(event_id: UUID, user_id: UUID, update: MemberStatusUpdate):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE event_members SET member_status = %s
        WHERE event_id = %s AND user_id = %s
        RETURNING event_id, user_id, member_status, joined_at
        """,
        (update.member_status, str(event_id), str(user_id))
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Membership not found")
    return member_row_to_dict(row)


def member_row_to_dict(row):
    return {
        "event_id": row[0],
        "user_id": row[1],
        "member_status": row[2],
        "joined_at": row[3],
    }