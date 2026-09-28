-- ============================================================
-- ShadowLink — PostgreSQL Schema
-- ⚠️  SYNTHETIC DATA ONLY — all actors, keys, wallets are fictional.
-- ============================================================

-- ────────────────────────────────────────────────────────────
-- Extensions
-- ────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "pgcrypto";      -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "pg_trgm";       -- trigram similarity indexes

-- ────────────────────────────────────────────────────────────
-- ENUM types
-- ────────────────────────────────────────────────────────────
DO $$ BEGIN
    CREATE TYPE risk_category AS ENUM (
        'DRUGS', 'ARMS', 'DATA', 'FINANCIAL', 'FRAUD', 'UNKNOWN'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE identifier_type AS ENUM (
        'PGP_KEY', 'WALLET_BTC', 'WALLET_ETH', 'EMAIL_HASH'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE infra_leak_type AS ENUM (
        'EXPOSED_STATUS', 'SSL_CERT_MATCH', 'SERVER_BANNER', 'DESCRIPTOR_MISMATCH'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE trust_link_type AS ENUM (
        'VOUCHED_FOR', 'SAME_WALLET', 'SAME_PGP', 'STYLE_MATCH'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ────────────────────────────────────────────────────────────
-- 1. actors
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS actors (
    id                UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    primary_handle    TEXT            NOT NULL,
    first_seen        TIMESTAMPTZ,
    last_seen         TIMESTAMPTZ,
    confidence_score  NUMERIC(5, 2)   NOT NULL DEFAULT 0,
    risk_category     risk_category   NOT NULL DEFAULT 'UNKNOWN',
    notes             TEXT,
    created_at        TIMESTAMPTZ     NOT NULL DEFAULT now()
);

-- ────────────────────────────────────────────────────────────
-- 2. aliases
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS aliases (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id        UUID            NOT NULL REFERENCES actors(id) ON DELETE CASCADE,
    handle          TEXT            NOT NULL,
    platform        TEXT            NOT NULL,
    active_from     TIMESTAMPTZ,
    active_to       TIMESTAMPTZ,

    CONSTRAINT uq_alias_handle_platform UNIQUE (handle, platform)
);

-- ────────────────────────────────────────────────────────────
-- 3. identifiers
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS identifiers (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id        UUID            NOT NULL REFERENCES actors(id) ON DELETE CASCADE,
    alias_id        UUID            REFERENCES aliases(id) ON DELETE SET NULL,
    type            identifier_type NOT NULL,
    value           TEXT            NOT NULL,
    first_seen      TIMESTAMPTZ,

    CONSTRAINT uq_identifier_type_value UNIQUE (type, value)
);

-- ────────────────────────────────────────────────────────────
-- 4. posts
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS posts (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    alias_id        UUID            NOT NULL REFERENCES aliases(id) ON DELETE CASCADE,
    platform        TEXT            NOT NULL,
    timestamp       TIMESTAMPTZ     NOT NULL,
    raw_text        TEXT,
    category        risk_category   NOT NULL DEFAULT 'UNKNOWN'
);

-- ────────────────────────────────────────────────────────────
-- 5. infra_leaks
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS infra_leaks (
    id                      UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id                UUID            NOT NULL REFERENCES actors(id) ON DELETE CASCADE,
    type                    infra_leak_type NOT NULL,
    onion_address           TEXT,
    matched_clearnet_ip     INET,
    matched_clearnet_domain TEXT,
    evidence                JSONB,
    confidence              NUMERIC(5, 2)   NOT NULL DEFAULT 0,
    detected_at             TIMESTAMPTZ     NOT NULL DEFAULT now()
);

-- ────────────────────────────────────────────────────────────
-- 6. trust_links
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS trust_links (
    id                  UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_a_id          UUID            NOT NULL REFERENCES actors(id) ON DELETE CASCADE,
    actor_b_id          UUID            NOT NULL REFERENCES actors(id) ON DELETE CASCADE,
    relationship_type   trust_link_type NOT NULL,
    strength_score      NUMERIC(5, 2)   NOT NULL DEFAULT 0,
    evidence            JSONB,
    ai_suggested        BOOLEAN         NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT uq_trust_link UNIQUE (actor_a_id, actor_b_id, relationship_type)
);

-- ────────────────────────────────────────────────────────────
-- 7. ingestion_log
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ingestion_log (
    id              BIGSERIAL       PRIMARY KEY,
    run_at          TIMESTAMPTZ     NOT NULL DEFAULT now(),
    module          TEXT            NOT NULL,
    status          TEXT            NOT NULL DEFAULT 'PENDING',
    summary         JSONB,
    duration_ms     INTEGER
);

-- ────────────────────────────────────────────────────────────
-- Indexes — foreign keys
-- ────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS ix_aliases_actor_id        ON aliases(actor_id);
CREATE INDEX IF NOT EXISTS ix_identifiers_actor_id    ON identifiers(actor_id);
CREATE INDEX IF NOT EXISTS ix_identifiers_alias_id    ON identifiers(alias_id);
CREATE INDEX IF NOT EXISTS ix_posts_alias_id          ON posts(alias_id);
CREATE INDEX IF NOT EXISTS ix_infra_leaks_actor_id    ON infra_leaks(actor_id);
CREATE INDEX IF NOT EXISTS ix_trust_links_actor_a_id  ON trust_links(actor_a_id);
CREATE INDEX IF NOT EXISTS ix_trust_links_actor_b_id  ON trust_links(actor_b_id);

-- ────────────────────────────────────────────────────────────
-- Indexes — GIN trigram (fuzzy search)
-- ────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS ix_aliases_handle_trgm
    ON aliases USING gin (handle gin_trgm_ops);

CREATE INDEX IF NOT EXISTS ix_identifiers_value_trgm
    ON identifiers USING gin (value gin_trgm_ops);
