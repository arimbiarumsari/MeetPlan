-- MeetPlan Database Schema
-- PostgreSQL
-- Diimplementasikan dari ERD hasil Worksheet Week 2 (Lab 2.4)
-- Issue #6: Merancang ERD dan skema basis data

-- Ekstensi untuk generate UUID (opsional, bisa pakai SERIAL/INT biasa juga)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =========================================================
-- USER
-- Menyimpan data akun pengguna (Member maupun Event Organizer)
-- =========================================================
CREATE TABLE users (
    user_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100) NOT NULL,
    email           VARCHAR(255) NOT NULL UNIQUE,
    password        VARCHAR(255) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT now()
);

-- =========================================================
-- EVENT
-- Menyimpan data acara yang dibuat oleh Event Organizer
-- =========================================================
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

-- =========================================================
-- EVENT_MEMBER
-- Relasi many-to-many antara USER dan EVENT (siapa ikut event apa)
-- =========================================================
CREATE TABLE event_members (
    event_id        UUID NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    joined_at       TIMESTAMP NOT NULL DEFAULT now(),
    member_status   VARCHAR(20) NOT NULL DEFAULT 'invited'
                    CHECK (member_status IN ('invited', 'joined', 'declined')),
    PRIMARY KEY (event_id, user_id)
);

-- =========================================================
-- AVAILABILITY
-- Jadwal tidak tersedia yang diinput tiap anggota per event
-- status: dikonsumsi langsung oleh scheduler (busy / available / tentative)
-- =========================================================
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

-- =========================================================
-- TIME_CANDIDATE
-- Kandidat waktu hasil perhitungan scheduler, dengan skor
-- =========================================================
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

-- =========================================================
-- CANCEL_REQUEST
-- Fitur "Pengen Cancel" anonim.
-- Identitas is_cancel per user TIDAK ditampilkan ke user lain di level aplikasi;
-- hanya agregat jumlah yang dibaca untuk menentukan status akhir event.
-- =========================================================
CREATE TABLE cancel_requests (
    cancel_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id        UUID NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    is_cancel       BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMP NOT NULL DEFAULT now(),
    UNIQUE (event_id, user_id)
);

-- =========================================================
-- POLL
-- Polling tempat/kegiatan per event
-- =========================================================
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

-- =========================================================
-- POLL_OPTION
-- Pilihan-pilihan dalam satu poll
-- =========================================================
CREATE TABLE poll_options (
    option_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    poll_id         UUID NOT NULL REFERENCES polls(poll_id) ON DELETE CASCADE,
    option_name     VARCHAR(150) NOT NULL,
    description     TEXT
);

-- =========================================================
-- VOTE
-- Suara tiap user terhadap satu poll_option
-- =========================================================
CREATE TABLE votes (
    vote_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    option_id       UUID NOT NULL REFERENCES poll_options(option_id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    voted_at        TIMESTAMP NOT NULL DEFAULT now(),
    UNIQUE (option_id, user_id)
);

-- =========================================================
-- INDEX tambahan untuk query yang sering dipakai
-- =========================================================
CREATE INDEX idx_availability_event ON availability(event_id);
CREATE INDEX idx_time_candidates_event ON time_candidates(event_id);
CREATE INDEX idx_cancel_requests_event ON cancel_requests(event_id);
CREATE INDEX idx_polls_event ON polls(event_id);
CREATE INDEX idx_votes_option ON votes(option_id);
