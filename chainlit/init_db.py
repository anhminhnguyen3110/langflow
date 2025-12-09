# -*- coding: utf-8 -*-
"""
Script to initialize Chainlit PostgreSQL database tables.
Run this once to create the required tables for data persistence.
"""

import psycopg2
import os
import re

# PostgreSQL connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://langflow:langflow@localhost:5432/chainlit")

# Parse connection string
# Format: postgresql://user:pass@host:port/dbname
match = re.match(r'postgresql(?:\+\w+)?://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', DATABASE_URL)
if match:
    DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME = match.groups()
else:
    DB_USER = "langflow"
    DB_PASS = "langflow"
    DB_HOST = "localhost"
    DB_PORT = "5432"
    DB_NAME = "chainlit"


# SQL to drop existing tables (for clean reinstall)
DROP_TABLES_SQL = """
DROP TABLE IF EXISTS feedbacks CASCADE;
DROP TABLE IF EXISTS elements CASCADE;
DROP TABLE IF EXISTS steps CASCADE;
DROP TABLE IF EXISTS threads CASCADE;
DROP TABLE IF EXISTS users CASCADE;
"""


# SQL statements to create Chainlit tables
CREATE_TABLES_SQL = """
-- Users table
CREATE TABLE users (
    "id" UUID PRIMARY KEY,
    "identifier" TEXT NOT NULL UNIQUE,
    "metadata" JSONB NOT NULL,
    "createdAt" TEXT
);

-- Threads table (chat sessions)
CREATE TABLE IF NOT EXISTS threads (
    "id" UUID PRIMARY KEY,
    "createdAt" TEXT,
    "name" TEXT,
    "userId" UUID,
    "userIdentifier" TEXT,
    "tags" TEXT[],
    "metadata" JSONB,
    FOREIGN KEY ("userId") REFERENCES users("id") ON DELETE CASCADE
);

-- Steps table (messages and actions)
CREATE TABLE IF NOT EXISTS steps (
    "id" UUID PRIMARY KEY,
    "name" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "threadId" UUID NOT NULL,
    "parentId" UUID,
    "streaming" BOOLEAN NOT NULL,
    "waitForAnswer" BOOLEAN,
    "isError" BOOLEAN,
    "metadata" JSONB,
    "tags" TEXT[],
    "input" TEXT,
    "output" TEXT,
    "createdAt" TEXT,
    "command" TEXT,
    "start" TEXT,
    "end" TEXT,
    "generation" JSONB,
    "showInput" TEXT,
    "language" TEXT,
    "indent" INT,
    "defaultOpen" BOOLEAN,
    FOREIGN KEY ("threadId") REFERENCES threads("id") ON DELETE CASCADE
);

-- Elements table (files, images, etc.)
CREATE TABLE IF NOT EXISTS elements (
    "id" UUID PRIMARY KEY,
    "threadId" UUID,
    "type" TEXT,
    "url" TEXT,
    "chainlitKey" TEXT,
    "name" TEXT NOT NULL,
    "display" TEXT,
    "objectKey" TEXT,
    "size" TEXT,
    "page" INT,
    "language" TEXT,
    "forId" UUID,
    "mime" TEXT,
    "props" JSONB,
    FOREIGN KEY ("threadId") REFERENCES threads("id") ON DELETE CASCADE
);

-- Feedback table
CREATE TABLE IF NOT EXISTS feedbacks (
    "id" UUID PRIMARY KEY,
    "forId" UUID NOT NULL,
    "threadId" UUID NOT NULL,
    "value" INT NOT NULL,
    "comment" TEXT,
    FOREIGN KEY ("threadId") REFERENCES threads("id") ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_identifier ON users("identifier");
CREATE INDEX IF NOT EXISTS idx_threads_userId ON threads("userId");
CREATE INDEX IF NOT EXISTS idx_threads_userIdentifier ON threads("userIdentifier");
CREATE INDEX IF NOT EXISTS idx_steps_threadId ON steps("threadId");
CREATE INDEX IF NOT EXISTS idx_steps_parentId ON steps("parentId");
CREATE INDEX IF NOT EXISTS idx_elements_threadId ON elements("threadId");
CREATE INDEX IF NOT EXISTS idx_elements_forId ON elements("forId");
CREATE INDEX IF NOT EXISTS idx_feedbacks_forId ON feedbacks("forId");
CREATE INDEX IF NOT EXISTS idx_feedbacks_threadId ON feedbacks("threadId");
"""


def init_database(drop_existing: bool = True):
    """
    Initialize the PostgreSQL database with required tables.
    
    Args:
        drop_existing: If True, drop existing tables before creating new ones
    """
    print(f"Connecting to PostgreSQL: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    try:
        # Drop existing tables if requested
        if drop_existing:
            print("Dropping existing tables...")
            cursor.execute(DROP_TABLES_SQL)
            print("  ✓ Dropped all existing tables")
        
        # Execute CREATE TABLE statements one by one
        print("\nCreating tables...")
        
        # Create users table
        cursor.execute("""
            CREATE TABLE users (
                "id" UUID PRIMARY KEY,
                "identifier" TEXT NOT NULL UNIQUE,
                "metadata" JSONB NOT NULL,
                "createdAt" TEXT
            )
        """)
        print("  ✓ Created table: users")
        
        # Create threads table
        cursor.execute("""
            CREATE TABLE threads (
                "id" UUID PRIMARY KEY,
                "createdAt" TEXT,
                "name" TEXT,
                "userId" UUID,
                "userIdentifier" TEXT,
                "tags" TEXT[],
                "metadata" JSONB,
                FOREIGN KEY ("userId") REFERENCES users("id") ON DELETE CASCADE
            )
        """)
        print("  ✓ Created table: threads")
        
        # Create steps table
        cursor.execute("""
            CREATE TABLE steps (
                "id" UUID PRIMARY KEY,
                "name" TEXT NOT NULL,
                "type" TEXT NOT NULL,
                "threadId" UUID NOT NULL,
                "parentId" UUID,
                "streaming" BOOLEAN NOT NULL,
                "waitForAnswer" BOOLEAN,
                "isError" BOOLEAN,
                "metadata" JSONB,
                "tags" TEXT[],
                "input" TEXT,
                "output" TEXT,
                "createdAt" TEXT,
                "command" TEXT,
                "start" TEXT,
                "end" TEXT,
                "generation" JSONB,
                "showInput" TEXT,
                "language" TEXT,
                "indent" INT,
                "defaultOpen" BOOLEAN,
                FOREIGN KEY ("threadId") REFERENCES threads("id") ON DELETE CASCADE
            )
        """)
        print("  ✓ Created table: steps")
        
        # Create elements table
        cursor.execute("""
            CREATE TABLE elements (
                "id" UUID PRIMARY KEY,
                "threadId" UUID,
                "type" TEXT,
                "url" TEXT,
                "chainlitKey" TEXT,
                "name" TEXT NOT NULL,
                "display" TEXT,
                "objectKey" TEXT,
                "size" TEXT,
                "page" INT,
                "language" TEXT,
                "forId" UUID,
                "mime" TEXT,
                "props" JSONB,
                FOREIGN KEY ("threadId") REFERENCES threads("id") ON DELETE CASCADE
            )
        """)
        print("  ✓ Created table: elements")
        
        # Create feedbacks table
        cursor.execute("""
            CREATE TABLE feedbacks (
                "id" UUID PRIMARY KEY,
                "forId" UUID NOT NULL,
                "threadId" UUID NOT NULL,
                "value" INT NOT NULL,
                "comment" TEXT,
                FOREIGN KEY ("threadId") REFERENCES threads("id") ON DELETE CASCADE
            )
        """)
        print("  ✓ Created table: feedbacks")
        
        # Create indexes
        print("\nCreating indexes...")
        indexes = [
            ('idx_users_identifier', 'users("identifier")'),
            ('idx_threads_userId', 'threads("userId")'),
            ('idx_threads_userIdentifier', 'threads("userIdentifier")'),
            ('idx_steps_threadId', 'steps("threadId")'),
            ('idx_steps_parentId', 'steps("parentId")'),
            ('idx_elements_threadId', 'elements("threadId")'),
            ('idx_elements_forId', 'elements("forId")'),
            ('idx_feedbacks_forId', 'feedbacks("forId")'),
            ('idx_feedbacks_threadId', 'feedbacks("threadId")'),
        ]
        for idx_name, idx_on in indexes:
            cursor.execute(f'CREATE INDEX IF NOT EXISTS {idx_name} ON {idx_on}')
            print(f"  ✓ Created index: {idx_name}")
        
        print("\n[OK] Database initialized successfully!")
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        print(f"\nTables in database: {[t[0] for t in tables]}")
        
        # Show table row counts
        print("\nTable row counts:")
        for table in tables:
            cursor.execute(f'SELECT COUNT(*) FROM "{table[0]}"')
            count = cursor.fetchone()[0]
            print(f"  {table[0]}: {count} rows")
        
    except Exception as e:
        print(f"\n[ERROR] Error initializing database: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    import sys
    
    # Check for --no-drop flag
    drop_existing = "--no-drop" not in sys.argv
    
    if drop_existing:
        print("⚠️  WARNING: This will DROP all existing tables and data!")
        print("    Use --no-drop to preserve existing tables.\n")
    
    init_database(drop_existing=drop_existing)

