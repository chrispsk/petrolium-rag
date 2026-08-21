from typing import TypedDict, NotRequired


class IngestionState(TypedDict):
    files: NotRequired[list]
    changed_files: NotRequired[list]
    documents: NotRequired[list]
    chunks: NotRequired[list]
    contextual_chunks: NotRequired[list]
    embeddings: NotRequired[list]
    indexed_files: NotRequired[list]
    failed_files: NotRequired[list]