"""
EarthScape Climate Agency - Database Module
Manages SQL Server LocalDB user persistence, bcrypt password hashing,
and demo account seeding.

Connection:  (localdb)\\MSSQLLocalDB
Database:    EarthScapeDb  (auto-created)
Driver:      ODBC Driver 18 for SQL Server
"""

import os
import pyodbc
import bcrypt

try:
    from src.data.static_data import DEMO_ACCOUNTS
except ImportError:
    from data.static_data import DEMO_ACCOUNTS
from datetime import datetime, timezone

# ── Connection helpers ────────────────────────────────────────────────

_DRIVER = "ODBC Driver 18 for SQL Server"
_SERVER = "(localdb)\\MSSQLLocalDB"
_DB_NAME = "EarthScapeDb"


def _connection_string(database: str | None = None) -> str:
    """Build an ODBC connection string. If *database* is None, connects to master."""
    db = database or _DB_NAME
    return (
        f"Driver={{{_DRIVER}}};"
        f"Server={_SERVER};"
        f"Database={db};"
        f"Trusted_Connection=yes;"
        f"TrustServerCertificate=yes;"
    )


def get_connection() -> pyodbc.Connection:
    """Return a connection to EarthScapeDb."""
    return pyodbc.connect(_connection_string(), autocommit=False)


def _ensure_database() -> None:
    """Create the EarthScapeDb database if it does not exist."""
    conn = pyodbc.connect(_connection_string("master"), autocommit=True)
    try:
        cur = conn.cursor()
        cur.execute(
            "IF DB_ID(?) IS NULL CREATE DATABASE [EarthScapeDb]",
            (_DB_NAME,)
        )
    finally:
        conn.close()


# ── Schema ────────────────────────────────────────────────────────────

def init_db() -> None:
    """Create the Users table if it does not already exist."""
    _ensure_database()
    conn = get_connection()
    try:
        conn.execute("""
            IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Users')
            CREATE TABLE Users (
                Id              INT IDENTITY(1,1) PRIMARY KEY,
                Name            NVARCHAR(200)  NOT NULL,
                Email           NVARCHAR(320)  NOT NULL,
                PasswordHash    NVARCHAR(200)  NOT NULL,
                Role            NVARCHAR(50)   NOT NULL DEFAULT 'analyst',
                CreatedAt       NVARCHAR(50)   NOT NULL
            )
        """)
        # Unique index on Email (case-insensitive via default collation)
        conn.execute("""
            IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UQ_Users_Email')
            CREATE UNIQUE INDEX UQ_Users_Email ON Users(Email)
        """)
        conn.commit()
    finally:
        conn.close()


# ── Password helpers ──────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ── User CRUD ─────────────────────────────────────────────────────────

def find_user_by_email(email: str) -> dict | None:
    """Look up a user by email (case-insensitive). Returns dict or None."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT Id, Name, Email, PasswordHash, Role, CreatedAt "
            "FROM Users WHERE LOWER(Email) = LOWER(?)",
            (email,)
        ).fetchone()
        if row is None:
            return None
        return {
            "Id": row.Id,
            "Name": row.Name,
            "Email": row.Email,
            "PasswordHash": row.PasswordHash,
            "Role": row.Role,
            "CreatedAt": row.CreatedAt,
        }
    finally:
        conn.close()


def create_user(name: str, email: str, password: str, role: str = "analyst") -> dict:
    """
    Insert a new user into SQL Server.
    Raises ValueError if the email already exists.
    Returns the created user dict (without PasswordHash).
    """
    conn = get_connection()
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        pw_hash = hash_password(password)
        conn.execute(
            "INSERT INTO Users (Name, Email, PasswordHash, Role, CreatedAt) "
            "VALUES (?, ?, ?, ?, ?)",
            (name, email.lower(), pw_hash, role, now)
        )
        conn.commit()
        return {
            "Name": name,
            "Email": email.lower(),
            "Role": role,
            "CreatedAt": now,
        }
    except pyodbc.IntegrityError:
        conn.rollback()
        raise ValueError("An account with this email already exists")
    finally:
        conn.close()


def list_users() -> list[dict]:
    """Return all users (without password hashes)."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT Id, Name, Email, Role, CreatedAt FROM Users ORDER BY Id"
        ).fetchall()
        return [
            {"Id": r.Id, "Name": r.Name, "Email": r.Email, "Role": r.Role, "CreatedAt": r.CreatedAt}
            for r in rows
        ]
    finally:
        conn.close()


# ── Seeding ───────────────────────────────────────────────────────────

def seed_demo_accounts() -> None:
    """
    Seed demo accounts only if they do not already exist.
    Creates exactly 1 Admin and 3 Analysts.
    """
    demo_accounts = DEMO_ACCOUNTS
    for acct in demo_accounts:
        if find_user_by_email(acct["email"]) is None:
            create_user(acct["name"], acct["email"], acct["password"], acct["role"])
            print(f"  Seeded demo account: {acct['email']} ({acct['role']})")


def init_and_seed() -> None:
    """Initialize the database and seed demo accounts. Called at server startup."""
    init_db()
    print("[DB] SQL Server LocalDB — EarthScapeDb initialized.")
    seed_demo_accounts()
    print("[DB] Demo accounts verified.")
