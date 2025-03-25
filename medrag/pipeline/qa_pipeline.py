from ollama import chat, ChatResponse
from langchain_huggingface import HuggingFaceEmbeddings
import sys
import os

parent_dir = os.path.abspath(os.path.join(os.path.dirname('.'), '..'))
sys.path.append(parent_dir)

from medrag.retrieval.vector_db import VectorDB
from medrag.retrieval.keyword_db import KeywordDB
from medrag.retrieval.reranking import rerank_documents
from medrag.summarization.summarization import QueryBasedTextRankSummarizer

class QAPipeline:
    def __init__(self, 
                 vector_database: VectorDB,
                 keyword_database: KeywordDB,
                 summarizer: QueryBasedTextRankSummarizer,
                 embedding_model: HuggingFaceEmbeddings,
                 k: int = 15):
        self.vector_database = vector_database
        self.keyword_database = keyword_database
        self.summarizer = summarizer
        self.embedding_model = embedding_model
        self.k = k


    def generate_response(self, query: str):
        #vector search
        results_vector, scores_vector  = self.vector_database.search(query, k=self.k)

        #keyword search
        results_keyword, scores_keyword = self.keyword_database.search(query, k=self.k)

        #reranking
        results_combined = results_vector + results_keyword
        reranked_results, reranked_scores = rerank_documents(query, retrieved_results=results_combined, model=self.embedding_model)

        # summarize texts
        summarized_texts, pmids, titles = self.summarizer.process(query, reranked_records=reranked_results)

        prompt = f"""
            Question: {query}\n\n
            Context based on the medical records of similar patients to provide health recommendations divided into paragraphs and generated lists:\n\n
            {summarized_texts}\n\n
            Sources:\n
            {chr(10).join([f"- {title} (PMID: {pmid})" for title, pmid in zip(titles, pmids)])}\n\n
            If the context does not contain the answer to the question, write 'The suggested context does not contain the answer to the question', and try to answer on your own, giving references to the sources you used. But do not make up anything—use only factual and trustworthy data.
        """

        response: ChatResponse = chat(model='llama3.2:3b', messages=[
            {
                "role": "system", 
                "content": """
                    You are an expert in producing health recommendations based on given content.    
                """
            },
            {
                "role": "user",
                "content": prompt
            },
        ])

        return response.message.content