# Third-party libraries
import numpy as np

# Local imports
from graph import nodes


# -------------------- Define evaluation queries --------------------

evaluation_queries = [
    {
        "query": "What is the minimum transaction size for DEF?",
        "relevant_source": "adblue-and-def.md",
        "relevant_path": "Diesel exhaust fluid (DEF)"
    },
    {
        "query": "How is DEF defined?",
        "relevant_source": "adblue-and-def.md",
        "relevant_path": "Diesel exhaust fluid (DEF)"
    },
    {
        "query": "How are transaction data verified?",
        "relevant_source": "adblue-and-def.md",
        "relevant_path": "Verification of transaction data"
    },
    {
        "query": "What primary tests are applied by reporters?",
        "relevant_source": "adblue-and-def.md",
        "relevant_path": "Primary tests applied by reporters"
    },
    {
        "query": "Who won the 2018 FIFA World Cup?",
        "relevant_source": None,
        "relevant_path": None
    }
]


# -------------------- Run evaluation queries --------------------

evaluation_results = []

for item in evaluation_queries:
    query = item["query"]
    relevant_source = item["relevant_source"]
    relevant_path = item["relevant_path"]

    state = {"query": query, "subqueries": [query]}

    retrieve_result = nodes.retrieve(state)
    state["retrieved_results"] = retrieve_result["retrieved_results"]

    rerank_result = nodes.rerank(state)
    top_documents = rerank_result["reranked_results"]

    retrieved_results = []

    for result_item in top_documents:
        document = result_item["document"]

        retrieved_results.append({
            "source": document[5],
            "path": document[3],
            "score": result_item["score"]
        })

    evaluation_results.append({
        "query": query,
        "relevant_source": relevant_source,
        "relevant_path": relevant_path,
        "retrieved": retrieved_results
    })


# -------------------- Display evaluation results --------------------

for result in evaluation_results:
    print("\nQuery:", result["query"])
    print("Relevant source:", result["relevant_source"])
    print("Relevant path:", result["relevant_path"])
    print("Retrieved:")

    if len(result["retrieved"]) == 0:
        print("No info")

    for item in result["retrieved"]:
        print("Source:", item["source"])
        print("Path:", item["path"])
        print("Score:", round(item["score"], 4))
        print()


# -------------------- Calculate evaluation metrics --------------------

precision_scores = []
recall_scores = []
mrr_scores = []

rejection_correct = 0
rejection_total = 0

K = 5


for result in evaluation_results:
    relevant_source = result["relevant_source"]
    relevant_path = result["relevant_path"]
    retrieved = result["retrieved"]

    if relevant_source is None:
        rejection_total += 1

        if len(retrieved) == 0:
            rejection_correct += 1

        continue

    correct = 0
    reciprocal_rank = 0

    for rank, item in enumerate(retrieved[:K], start=1):
        source_match = item["source"] == relevant_source
        path_match = relevant_path in item["path"]

        if source_match and path_match:
            correct += 1

            if reciprocal_rank == 0:
                reciprocal_rank = 1 / rank

    precision = correct / K

    if correct > 0:
        recall = 1
    else:
        recall = 0

    precision_scores.append(precision)
    recall_scores.append(recall)
    mrr_scores.append(reciprocal_rank)


# -------------------- Final metrics --------------------

if rejection_total > 0:
    rejection_accuracy = rejection_correct / rejection_total
else:
    rejection_accuracy = 0


print("\n----------------------------------------")
print("FINAL EVALUATION")
print("----------------------------------------")
print("Precision@5:", round(np.mean(precision_scores), 3))
print("Recall@5:", round(np.mean(recall_scores), 3))
print("MRR:", round(np.mean(mrr_scores), 3))
print("Rejection Accuracy:", round(rejection_accuracy, 3))