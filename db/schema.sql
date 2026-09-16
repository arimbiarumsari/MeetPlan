-- schema database MeetPlan, PostgreSQL
-- implementasi dari ERD yang sudah disusun pada Week 2 (issue #6)

CREATE EXTENSION IF NOT EXISTS "pgcrypto"; -- untuk gen_random_uuid()

-- data akun pengguna
CREATE TABLE users (
    user_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100) NOT NULL,
    email           VARCHAR(255) NOT NULL UNIQUE,
    password        VARCHAR(255) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT now()
);

-- acara yang dibuat oleh organizer
CREATE TABLE events (
    event_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organizer_id    UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    event_name      VARCHAR(150) NOT NULL,
    description     TEXT,
    duration        INTERVAL,
    final_time      TIMESTAMP,
    final_location  VARCHAR(255),
    final_activity  VARCHAR(255),
    status          VARCHAR(20) NOT NULL DEFAULT 'draft'
                    CHECK (status IN ('draft', 'active', 'finalized', 'cancelled')),
    created_at      TIMESTAMP NOT NULL DEFAULT now()
);

-- relasi user dan event, many-to-many
CREATE TABLE event_members (
    event_id        UUID NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    joined_at       TIMESTAMP NOT NULL DEFAULT now(),
    member_status   VARCHAR(20) NOT NULL DEFAULT 'invited'
                    CHECK (member_status IN ('invited', 'joined', 'declined')),
    PRIMARY KEY (event_id, user_id)
);

-- jadwal ketersediaan tiap anggota per event
-- kolom status di sini yang dipakai langsung oleh scheduler (busy/available/tentative)
CREATE TABLE availability (
    availability_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id        UUID NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    start_time      TIMESTAMP NOT NULL,
    end_time        TIMESTAMP NOT NULL,
    status          VARCHAR(20) NOT NULL
                    CHECK (status IN ('busy', 'available', 'tentative')),
    CHECK (end_time > start_time)
);

-- hasil kandidat waktu dari scheduler beserta skornya
CREATE TABLE time_candidates (
    candidate_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id        UUID NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
    start_time      TIMESTAMP NOT NULL,
    end_time        TIMESTAMP NOT NULL,
    score           NUMERIC(4,2) NOT NULL DEFAULT 0,
    status          VARCHAR(20) NOT NULL DEFAULT 'proposed'
                    CHECK (status IN ('proposed', 'selected', 'rejected')),
    CHECK (end_time > start_time)
);

-- fitur "Pengen Cancel" yang bersifat anonim
-- nilai is_cancel per user tidak ditampilkan ke anggota lain, hanya dihitung
-- jumlahnya untuk menentukan apakah event dibatalkan atau tetap berjalan
CREATE TABLE cancel_requests (
    cancel_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id        UUID NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    is_cancel       BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMP NOT NULL DEFAULT now(),
    UNIQUE (event_id, user_id)
);

-- polling tempat atau kegiatan
CREATE TABLE polls (
    poll_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id        UUID NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
    title           VARCHAR(150) NOT NULL,
    type            VARCHAR(20) NOT NULL DEFAULT 'location'
                    CHECK (type IN ('location', 'activity')),
    status          VARCHAR(20) NOT NULL DEFAULT 'open'
                    CHECK (status IN ('open', 'closed')),
    created_at      TIMESTAMP NOT NULL DEFAULT now()
);

-- pilihan-pilihan pada satu poll
CREATE TABLE poll_options (
    option_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    poll_id         UUID NOT NULL REFERENCES polls(poll_id) ON DELETE CASCADE,
    option_name     VARCHAR(150) NOT NULL,
    description     TEXT
);

-- suara user terhadap satu poll_option
CREATE TABLE votes (
    vote_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    option_id       UUID NOT NULL REFERENCES poll_options(option_id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    voted_at        TIMESTAMP NOT NULL DEFAULT now(),
    UNIQUE (option_id, user_id)
);

-- index tambahan untuk query yang sering digunakan
CREATE INDEX idx_availability_event ON availability(event_id);
CREATE INDEX idx_time_candidates_event ON time_candidates(event_id);
CREATE INDEX idx_cancel_requests_event ON cancel_requests(event_id);
CREATE INDEX idx_polls_event ON polls(event_id);
CREATE INDEX idx_votes_option ON votes(option_id);
