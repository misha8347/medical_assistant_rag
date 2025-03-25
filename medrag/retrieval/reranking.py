from langchain_huggingface import HuggingFaceEmbeddings
import numpy as np
from typing import List

def rerank_documents(query: str, retrieved_results: List[str], model: HuggingFaceEmbeddings, top_k: int = 15):
    retrieved_docs = [result['chunk'] for result in retrieved_results]
    query_embedding = model.embed_query(query)
    doc_embeddings = model.embed_documents(retrieved_docs)

    similarity_scores = np.dot(doc_embeddings, query_embedding)  # Vector dot product
    reranked_docs = sorted(zip(retrieved_docs, similarity_scores), key=lambda x: x[1], reverse=True)

    top_k_reranked_docs = reranked_docs[:top_k]
    top_k_reranked_texts = [doc[0] for doc in top_k_reranked_docs]

    top_k_reranked_results = [result for result in retrieved_results if result['chunk'] in top_k_reranked_texts]
    top_k_reranked_scores = [doc[1] for doc in top_k_reranked_docs]

    return top_k_reranked_results, top_k_reranked_scores