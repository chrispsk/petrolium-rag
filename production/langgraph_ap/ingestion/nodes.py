from pathlib import Path
import hashlib
import asyncio
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter


SOURCE_PATH = Path("D:/RAG/petrolium/data")


class IngestionNodes:

    def __init__(self, pool, embedding_model):
        self.pool = pool
        self.embedding_model = embedding_model

    def scan_files(self, state):
        files = []

        for file_path in SOURCE_PATH.rglob("*.md"):
            files.append(str(file_path))

        print("\nFILES FOUND:", len(files))

        for file_path in files:
            print(file_path)

        return {"files": files}

    def get_file_hash(self, file_path):
        with open(file_path, "rb") as file:
            return hashlib.sha256(file.read()).hexdigest()

    async def detect_changes(self, state):
        files = state["files"]
        changed_files = []

        async with self.pool.connection() as connection:
            async with connection.cursor() as cursor:
                for file_path in files:
                    file_path = Path(file_path)
                    file_hash = self.get_file_hash(file_path)

                    await cursor.execute("SELECT file_hash FROM documents WHERE filename = %s;", (file_path.name,))
                    result = await cursor.fetchone()

                    if result is None:
                        print("New:", file_path.name)
                        changed_files.append({"path": str(file_path), "hash": file_hash})

                    elif result[0] != file_hash:
                        print("Modified:", file_path.name)
                        changed_files.append({"path": str(file_path), "hash": file_hash})

                    else:
                        print("Skipping unchanged:", file_path.name)

        return {"changed_files": changed_files}

    async def load_documents(self, state):
        changed_files = state["changed_files"]
        documents = []

        for file_info in changed_files:
            file_path = Path(file_info["path"])

            content = await asyncio.to_thread(
                file_path.read_text,
                encoding="utf-8",
                errors="replace"
            )

            documents.append({
                "path": str(file_path),
                "filename": file_path.name,
                "hash": file_info["hash"],
                "content": content
            })

            print("\nLOADED:", file_path.name)
            print("Characters:", len(content))
            print("Words:", len(content.split()))

        return {"documents": documents}

    def chunk_documents(self, state):
        documents = state["documents"]

        headers_to_split_on = [
            ("#", "document_title"),
            ("##", "section"),
            ("###", "subsection"),
            ("####", "subsubsection"),
            ("#####", "detail")
        ]

        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on, strip_headers=False)
        recursive_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)

        sections = []

        for document in documents:
            file_sections = markdown_splitter.split_text(document["content"])

            for section in file_sections:
                section.metadata["source"] = document["filename"]
                section.metadata["file_hash"] = document["hash"]

                heading_parts = [
                    section.metadata.get("document_title"),
                    section.metadata.get("section"),
                    section.metadata.get("subsection"),
                    section.metadata.get("subsubsection"),
                    section.metadata.get("detail")
                ]

                heading_path = []

                for part in heading_parts:
                    if part:
                        heading_path.append(part)

                section.metadata["heading_path"] = " > ".join(heading_path)
                sections.append(section)

            print("\nSECTIONS:", document["filename"], len(file_sections))

        final_sections = []

        for section in sections:
            if len(section.page_content) > 1800:
                split_sections = recursive_splitter.split_documents([section])

                for split_section in split_sections:
                    final_sections.append(split_section)
            else:
                final_sections.append(section)

        chunks = []

        for index, section in enumerate(final_sections):
            chunks.append({
                "chunk_id": index,
                "source": section.metadata["source"],
                "file_hash": section.metadata["file_hash"],
                "heading_path": section.metadata["heading_path"],
                "content": section.page_content
            })

        print("\nORIGINAL SECTIONS:", len(sections))
        print("FINAL CHUNKS:", len(chunks))

        return {"chunks": chunks}

    def contextualize_chunks(self, state):
        chunks = state["chunks"]
        contextual_chunks = []

        for chunk in chunks:
            contextual_content = "Source: " + chunk["source"] + "\n"
            contextual_content += "Context: " + chunk["heading_path"] + "\n\n"
            contextual_content += chunk["content"]

            contextual_chunks.append({
                "chunk_id": chunk["chunk_id"],
                "source": chunk["source"],
                "file_hash": chunk["file_hash"],
                "heading_path": chunk["heading_path"],
                "content": contextual_content
            })

        print("\nCONTEXTUAL CHUNKS:", len(contextual_chunks))

        return {"contextual_chunks": contextual_chunks}

    async def embed_chunks(self, state):
        contextual_chunks = state["contextual_chunks"]

        if len(contextual_chunks) == 0:
            return {"embeddings": []}

        texts = [chunk["content"] for chunk in contextual_chunks]

        embeddings = await asyncio.to_thread(self.embedding_model.embed_documents, texts)

        print("\nEMBEDDINGS GENERATED:", len(embeddings))

        if embeddings:
            print("DIMENSIONS:", len(embeddings[0]))

        return {"embeddings": embeddings}

    async def save_to_database(self, state):
        documents = state["documents"]
        chunks = state["contextual_chunks"]
        embeddings = state["embeddings"]

        indexed_files = []
        failed_files = []

        for document in documents:
            filename = document["filename"]
            file_hash = document["hash"]

            chunk_indices = [index for index, chunk in enumerate(chunks) if chunk["source"] == filename]

            try:
                async with self.pool.connection() as connection:
                    async with connection.cursor() as cursor:
                        await cursor.execute("SELECT id FROM documents WHERE filename = %s;", (filename,))
                        result = await cursor.fetchone()

                        if result is not None:
                            await cursor.execute("DELETE FROM documents WHERE id = %s;", (result[0],))

                        await cursor.execute("INSERT INTO documents (filename, file_hash) VALUES (%s, %s) RETURNING id;", (filename, file_hash))
                        document_id = (await cursor.fetchone())[0]

                        for chunk_id, index in enumerate(chunk_indices):
                            chunk = chunks[index]
                            embedding = embeddings[index]

                            await cursor.execute(
                                """
                                INSERT INTO chunks (document_id, chunk_id, heading_path, content, embedding)
                                VALUES (%s, %s, %s, %s, %s);
                                """,
                                (document_id, chunk_id, chunk["heading_path"], chunk["content"], embedding)
                            )

                        await connection.commit()

                indexed_files.append(filename)
                print("Indexed:", filename)

            except Exception as error:
                failed_files.append(filename)
                print("Failed:", filename, error)

        return {"indexed_files": indexed_files, "failed_files": failed_files}