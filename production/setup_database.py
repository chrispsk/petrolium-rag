# Third-party libraries
import psycopg

from pgvector.psycopg import register_vector


# -------------------- PostgreSQL connection --------------------

connection = psycopg.connect(dbname="postgres", user="postgres", password="root", host="localhost", port="5432")
cursor = connection.cursor()
print("Connected to PostgreSQL.")

# -------------------- Enable pgvector --------------------

cursor.execute("""CREATE EXTENSION IF NOT EXISTS vector;""")
connection.commit()
register_vector(connection)
print("pgvector enabled.\n")

# -------------------- Documents table --------------------

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS documents (
        id BIGSERIAL PRIMARY KEY,
        filename TEXT UNIQUE NOT NULL,
        file_hash TEXT NOT NULL,
        indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
)

connection.commit()
print("Documents table ready.")

# -------------------- Chunks table --------------------

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS chunks (
        id BIGSERIAL PRIMARY KEY,
        document_id BIGINT NOT NULL
            REFERENCES documents(id)
            ON DELETE CASCADE,
        chunk_id INTEGER NOT NULL,
        heading_path TEXT,
        content TEXT NOT NULL,
        embedding VECTOR(768) NOT NULL
    );
    """
)

connection.commit()
print("Chunks table ready.")

# -------------------- Semantic cache table --------------------

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS semantic_cache (
        id BIGSERIAL PRIMARY KEY,
        query TEXT NOT NULL,
        query_embedding VECTOR(768) NOT NULL,
        answer TEXT NOT NULL,
        subqueries JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
)

connection.commit()
print("Semantic cache table ready.\n")

# -------------------- Chunks vector index --------------------

cursor.execute(
    """
    CREATE INDEX IF NOT EXISTS chunks_embedding_idx
    ON chunks
    USING hnsw (embedding vector_cosine_ops);
    """
)

connection.commit()
print("Chunks vector index ready.")

# -------------------- Semantic cache vector index --------------------

cursor.execute(
    """
    CREATE INDEX IF NOT EXISTS semantic_cache_embedding_idx
    ON semantic_cache
    USING hnsw (query_embedding vector_cosine_ops);
    """
)

connection.commit()
print("Semantic cache vector index ready.")

# -------------------- Document ID index --------------------

cursor.execute(
    """
    CREATE INDEX IF NOT EXISTS chunks_document_id_idx
    ON chunks (document_id);
    """
)

connection.commit()
print("Document ID index ready.")

# -------------------- Check created tables --------------------

cursor.execute(
    """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    ORDER BY table_name;
    """
)

tables = cursor.fetchall()
print("\nCreated tables:")

for table in tables:
    print(table[0])

# -------------------- Close connection --------------------

cursor.close()
connection.close()
print("\nDatabase setup complete.")