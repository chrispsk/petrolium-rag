import torch
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langgraph.graph import START, END, StateGraph

from langgraph.checkpoint.memory import InMemorySaver

from sentence_transformers import CrossEncoder
from state import RAGState, RAGInput
from nodes import RAGNodes

# from database import pool  # production
from studio_database import studio_pool as pool  # Studio


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# -------------------- Models --------------------

print("Loading embedding model...")

embedding_model = HuggingFaceEmbeddings(
    model_name="BAAI/bge-base-en-v1.5",
    model_kwargs={"device": DEVICE},
    encode_kwargs={"normalize_embeddings": True}
)


print("Loading reranker...")
reranker = CrossEncoder("BAAI/bge-reranker-base", device=DEVICE)

print("Loading final LLM...")
llm = ChatOllama(model="qwen2.5:7b", temperature=0)

print("Loading decomposer...")
decomposer = llm

# -------------------- Nodes --------------------

nodes = RAGNodes(embedding_model=embedding_model, reranker=reranker, llm=llm, decomposer=decomposer, pool=pool)

def route_cache(state):
    if state["cache_hit"]:
        return "cached"

    return "retrieve"

def route_generation(state):
    if state["complete"]:
        return "save_cache"

    return "end"

def route_understanding(state):
    if state["intent"] in ["greeting", "polite", "conversation"]:
        return "chat_response"

    if state["retry"]:
        return "retrieve"

    return "check_cache"
# -------------------- Graph --------------------

graph = StateGraph(RAGState, input_schema=RAGInput)

graph.add_node("add_user_message", nodes.add_user_message)
graph.add_node("understand_query", nodes.understand_query)
graph.add_node("chat_response", nodes.chat_response)
graph.add_node("check_cache", nodes.check_cache)
graph.add_node("retrieve", nodes.retrieve)
graph.add_node("rerank", nodes.rerank)
graph.add_node("generate", nodes.generate)
graph.add_node("save_cache", nodes.save_cache)

graph.add_edge(START, "add_user_message")
graph.add_edge("add_user_message", "understand_query")
graph.add_conditional_edges("understand_query", route_understanding, {"chat_response": "chat_response", "retrieve": "retrieve", "check_cache": "check_cache"})
graph.add_edge("chat_response", END)
graph.add_conditional_edges("check_cache", route_cache, {"cached": END, "retrieve": "retrieve"})
graph.add_edge("retrieve", "rerank")
graph.add_edge("rerank", "generate")
graph.add_conditional_edges("generate", route_generation, {"save_cache": "save_cache", "end": END})
graph.add_edge("save_cache", END)

# For production
#checkpointer = InMemorySaver()
#app = graph.compile(checkpointer=checkpointer)

# For Studio
app = graph.compile()

