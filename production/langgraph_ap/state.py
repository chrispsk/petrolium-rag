from typing_extensions import TypedDict
from langgraph.graph import MessagesState


class RAGInput(TypedDict):
    query: str


class RAGState(MessagesState):
    query: str
    subqueries: list[str]
    retrieved_results: list
    reranked_results: list
    answer: str
    sources: list
    cache_hit: bool
    complete: bool
    retrieve: bool
    retry: bool
    intent: str
    last_subqueries: list[str]
    cache_saved: bool
    cache_score: float
    cache_reason: str