import torch
from langchain_huggingface import HuggingFaceEmbeddings
from langgraph.graph import START, END, StateGraph

# for production (FastAPI)
#from database import pool
# for development (Studio)
from studio_database import studio_pool as pool

from ingestion.state import IngestionState
from ingestion.nodes import IngestionNodes


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

embedding_model = HuggingFaceEmbeddings(
    model_name="BAAI/bge-base-en-v1.5",
    model_kwargs={"device": DEVICE},
    encode_kwargs={"normalize_embeddings": True}
)

nodes = IngestionNodes(pool=pool, embedding_model=embedding_model)

graph = StateGraph(IngestionState)

graph.add_node("scan_files", nodes.scan_files)
graph.add_node("detect_changes", nodes.detect_changes)
graph.add_node("load_documents", nodes.load_documents)
graph.add_node("chunk_documents", nodes.chunk_documents)
graph.add_node("contextualize_chunks", nodes.contextualize_chunks)
graph.add_node("embed_chunks", nodes.embed_chunks)
graph.add_node("save_to_database", nodes.save_to_database)

graph.add_edge(START, "scan_files")
graph.add_edge("scan_files", "detect_changes")
graph.add_edge("detect_changes", "load_documents")
graph.add_edge("load_documents", "chunk_documents")
graph.add_edge("chunk_documents", "contextualize_chunks")
graph.add_edge("contextualize_chunks", "embed_chunks")
graph.add_edge("embed_chunks", "save_to_database")
graph.add_edge("save_to_database", END)

app = graph.compile()