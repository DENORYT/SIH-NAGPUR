from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
import json
from pathlib import Path
from sqlalchemy import text
from app.models.database import engine, SessionLocal
import app.models.database as db_mod

from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

app = FastAPI(title="ShadowLink API", description="ShadowLink REST API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Mount Frontend directory statically
frontend_path = Path(__file__).parent.parent.parent / "frontend"
app.mount("/ui", StaticFiles(directory=str(frontend_path), html=True), name="ui")

@app.get("/")
def root():
    return RedirectResponse(url="/ui/")

def init_db():
    try:
        # Check postgres
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Connected to PostgreSQL.")
    except Exception as e:
        print(f"PostgreSQL not reachable. Falling back to SQLite.")
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        sqlite_url = "sqlite:///./shadowlink.db"
        sqlite_engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
        db_mod.engine = sqlite_engine
        db_mod.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sqlite_engine)
        
        # Apply simplified schema
        schema = """
        CREATE TABLE IF NOT EXISTS actors (
            id TEXT PRIMARY KEY,
            primary_handle TEXT NOT NULL,
            first_seen TEXT,
            last_seen TEXT,
            confidence_score REAL NOT NULL DEFAULT 0,
            risk_category TEXT NOT NULL DEFAULT 'UNKNOWN',
            notes TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS aliases (
            id TEXT PRIMARY KEY,
            actor_id TEXT NOT NULL,
            handle TEXT NOT NULL,
            platform TEXT NOT NULL,
            active_from TEXT,
            active_to TEXT,
            CONSTRAINT uq_alias_handle_platform UNIQUE (handle, platform)
        );

        CREATE TABLE IF NOT EXISTS identifiers (
            id TEXT PRIMARY KEY,
            actor_id TEXT NOT NULL,
            alias_id TEXT,
            type TEXT NOT NULL,
            value TEXT NOT NULL,
            first_seen TEXT
        );

        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            alias_id TEXT NOT NULL,
            platform TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            raw_text TEXT,
            category TEXT NOT NULL DEFAULT 'UNKNOWN'
        );

        CREATE TABLE IF NOT EXISTS infra_leaks (
            id TEXT PRIMARY KEY,
            actor_id TEXT NOT NULL,
            type TEXT NOT NULL,
            onion_address TEXT,
            matched_clearnet_ip TEXT,
            matched_clearnet_domain TEXT,
            evidence TEXT,
            confidence REAL NOT NULL DEFAULT 0,
            detected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS trust_links (
            id TEXT PRIMARY KEY,
            actor_a_id TEXT NOT NULL,
            actor_b_id TEXT NOT NULL,
            relationship_type TEXT NOT NULL,
            strength_score REAL NOT NULL DEFAULT 0,
            evidence TEXT,
            ai_suggested INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT uq_trust_link UNIQUE (actor_a_id, actor_b_id, relationship_type)
        );

        CREATE TABLE IF NOT EXISTS ingestion_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            module TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDING',
            summary TEXT,
            duration_ms INTEGER
        );
        """
        
        with sqlite_engine.connect() as conn:
            for statement in schema.split(';'):
                if statement.strip():
                    conn.execute(text(statement))
            conn.commit()
            
        print("SQLite schema created. Loading seed data...")
        seed_path = Path(__file__).resolve().parent / "seed" / "seed_dataset.json"
        
        if seed_path.exists():
            with db_mod.SessionLocal() as session:
                # check if empty
                count = session.execute(text("SELECT COUNT(*) FROM actors")).scalar()
                if count == 0:
                    with open(seed_path, 'r', encoding='utf-8') as f:
                        seed_data = json.load(f)
                    
                    for actor in seed_data.get("actors", []):
                        session.execute(text("""
                            INSERT INTO actors (id, primary_handle, first_seen, last_seen, confidence_score, risk_category, notes)
                            VALUES (:id, :handle, :fs, :ls, :cs, :rc, :notes)
                        """), {
                            "id": actor["id"],
                            "handle": actor["primary_handle"],
                            "fs": actor.get("first_seen"),
                            "ls": actor.get("last_seen"),
                            "cs": actor.get("confidence_score", 0),
                            "rc": actor.get("risk_category", "UNKNOWN"),
                            "notes": actor.get("notes")
                        })
                        
                        for alias in actor.get("aliases", []):
                            session.execute(text("""
                                INSERT INTO aliases (id, actor_id, handle, platform, active_from, active_to)
                                VALUES (:id, :aid, :h, :p, :af, :at)
                            """), {
                                "id": alias["id"],
                                "aid": actor["id"],
                                "h": alias["handle"],
                                "p": alias["platform"],
                                "af": alias.get("active_from"),
                                "at": alias.get("active_to")
                            })
                            
                            for ident in alias.get("identifiers", []):
                                session.execute(text("""
                                    INSERT INTO identifiers (id, actor_id, alias_id, type, value, first_seen)
                                    VALUES (:id, :aid, :alid, :t, :v, :fs)
                                """), {
                                    "id": ident["id"],
                                    "aid": actor["id"],
                                    "alid": alias["id"],
                                    "t": ident["type"],
                                    "v": ident["value"],
                                    "fs": ident.get("first_seen")
                                })
                                
                            for post in alias.get("posts", []):
                                session.execute(text("""
                                    INSERT INTO posts (id, alias_id, platform, timestamp, raw_text, category)
                                    VALUES (:id, :alid, :p, :t, :rt, :c)
                                """), {
                                    "id": post["id"],
                                    "alid": alias["id"],
                                    "p": post["platform"],
                                    "t": post["timestamp"],
                                    "rt": post.get("raw_text"),
                                    "c": post.get("category", "UNKNOWN")
                                })
                                
                    session.commit()
                    print("Seed data loaded.")
                    
                    print("Running modules...")
                    try:
                        from app.modules.infra_matcher import run as run_infra
                        from app.modules.identity_graph import run as run_identity
                        from app.modules.stylometry import run as run_stylometry
                        
                        run_infra(session)
                        run_identity(session)
                        run_stylometry(session)
                    except Exception as e:
                        print(f"Error running modules: {e}")
                else:
                    print("Seed data already loaded.")
        else:
            print("Seed data file not found.")

@app.on_event("startup")
def startup_event():
    init_db()
