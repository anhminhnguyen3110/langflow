# -*- coding: utf-8 -*-
"""
Script to initialize Chainlit PostgreSQL database tables.
Run this once to create the required tables for data persistence.
"""

import psycopg2
import os

# PostgreSQL connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://langflow:langflow@localhost:5432/chainlit")

# Parse connection string
# Format: postgresql://user:pass@host:port/dbname
import re
match = re.match(r'postgresql(?:\+\w+)?://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', DATABASE_URL)
if match:
    DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME = match.groups()
else:
    DB_USER = "langflow"
    DB_PASS = "langflow"
    DB_HOST = "localhost"
    DB_PORT = "5432"
    DB_NAME = "chainlit"

# SQL statements to create Chainlit tables (PostgreSQL compatible)
CREATE_TABLES_SQL = """
-- Users table
CREATE TABLE IF NOT EXISTS users (
    "id" TEXT PRIMARY KEY,
    "identifier" TEXT UNIQUE NOT NULL,
    "createdAt" TEXT DEFAULT CURRENT_TIMESTAMP,
    "metadata" JSONB DEFAULT '{}'
);

-- Threads table (chat sessions)
CREATE TABLE IF NOT EXISTS threads (
    "id" TEXT PRIMARY KEY,
    "name" TEXT,
    "userId" TEXT,
    "userIdentifier" TEXT,
    "createdAt" TEXT DEFAULT CURRENT_TIMESTAMP,
    "tags" TEXT[] DEFAULT '{}',
    "metadata" JSONB DEFAULT '{}'
);

-- Steps table (messages and actions) - Full schema for Chainlit
CREATE TABLE IF NOT EXISTS steps (
    "id" TEXT PRIMARY KEY,
    "threadId" TEXT NOT NULL,
    "parentId" TEXT,
    "name" TEXT,
    "type" TEXT NOT NULL,
    "input" TEXT,
    "output" TEXT,
    "isError" BOOLEAN DEFAULT FALSE,
    "createdAt" TEXT DEFAULT CURRENT_TIMESTAMP,
    "start" TEXT,
    "end" TEXT,
    "streaming" BOOLEAN DEFAULT FALSE,
    "waitForAnswer" BOOLEAN DEFAULT FALSE,
    "metadata" JSONB DEFAULT '{}',
    "generation" JSONB,
    "showInput" TEXT,
    "language" TEXT,
    "tags" TEXT[] DEFAULT '{}',
    "defaultOpen" BOOLEAN DEFAULT FALSE
);

-- Elements table (files, images, etc.)
CREATE TABLE IF NOT EXISTS elements (
    "id" TEXT PRIMARY KEY,
    "threadId" TEXT,
    "stepId" TEXT,
    "type" TEXT NOT NULL,
    "name" TEXT,
    "display" TEXT,
    "url" TEXT,
    "objectKey" TEXT,
    "size" TEXT,
    "page" INTEGER,
    "language" TEXT,
    "mime" TEXT,
    "forId" TEXT,
    "chainlitKey" TEXT,
    "props" JSONB DEFAULT '{}'
);

-- Feedback table
CREATE TABLE IF NOT EXISTS feedbacks (
    "id" TEXT PRIMARY KEY,
    "forId" TEXT NOT NULL,
    "value" INTEGER NOT NULL,
    "strategy" TEXT,
    "comment" TEXT
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_threads_userId ON threads("userId");
CREATE INDEX IF NOT EXISTS idx_threads_userIdentifier ON threads("userIdentifier");
CREATE INDEX IF NOT EXISTS idx_steps_threadId ON steps("threadId");
CREATE INDEX IF NOT EXISTS idx_steps_parentId ON steps("parentId");
CREATE INDEX IF NOT EXISTS idx_elements_threadId ON elements("threadId");
CREATE INDEX IF NOT EXISTS idx_elements_stepId ON elements("stepId");
CREATE INDEX IF NOT EXISTS idx_feedbacks_forId ON feedbacks("forId");
"""

def init_database():
    """Initialize the PostgreSQL database with required tables."""
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
        # Execute all CREATE TABLE statements
        for statement in CREATE_TABLES_SQL.split(';'):
            statement = statement.strip()
            if statement:
                try:
                    cursor.execute(statement)
                except Exception as e:
                    print(f"Warning: {e}")
        
        print("[OK] Database tables created successfully!")
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        print(f"Tables in database: {[t[0] for t in tables]}")
        
    except Exception as e:
        print(f"[ERROR] Error creating tables: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    init_database()

