from ollama import chat, ChatResponse
from langchain_huggingface import HuggingFaceEmbeddings
import sys
import os
import time
import logging

# Настройка логгера (можно настроить под себя)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

    #HyDE
    def generate_hypothetical_document(self, query: str):
        prompt_template = f"""Please answer the user's question in 2-4 sentences
        Question: {query}
        Answer:"""

        # model_name = 'llama3.2:3b'
        model_name = 'alibayram/medgemma'
        response: ChatResponse = chat(model=model_name, messages=[
            {
                "role": "system", 
                "content": """
                    Write a short text that answers the question:   
                """
            },
            {
                "role": "user",
                "content": prompt_template
            },
        ])
        return response.message.content

    def generate_response(self, query: str):
        start_total = time.time()

        # HyDE
        logger.info(f'query before hyde: {query}')
        start = time.time()
        query = self.generate_hypothetical_document(query)
        logger.info(f'query after hyde: {query}')
        logger.info(f"HyDE took {time.time() - start:.2f} seconds")

        # Vector search
        start = time.time()
        results_vector, scores_vector = self.vector_database.search(query, k=self.k)
        logger.info(f"Vector search took {time.time() - start:.2f} seconds")

        # Keyword search
        start = time.time()
        results_keyword, scores_keyword = self.keyword_database.search(query, k=self.k)
        logger.info(f"Keyword search took {time.time() - start:.2f} seconds")

        # Reranking
        start = time.time()
        results_combined = results_vector + results_keyword
        reranked_results, reranked_scores = rerank_documents(query, retrieved_results=results_combined, model=self.embedding_model)
        logger.info(f"Reranking took {time.time() - start:.2f} seconds")

        # Summarization
        start = time.time()
        summarized_texts, pmids, titles = self.summarizer.process(query, reranked_records=reranked_results)
        logger.info(f"Summarization took {time.time() - start:.2f} seconds")

        # Prompt preparation and LLM call
        prompt = f"""
            Question: {query}\n\n
            If question is not from medical domain simply say that it is not a medical question.
            Context based on the medical records of similar patients to provide health recommendations divided into paragraphs and generated lists:\n\n
            {summarized_texts}\n\n
            Sources:\n
            {chr(10).join([f"- {title} (Link: https://pubmed.ncbi.nlm.nih.gov/{pmid}/)" for title, pmid in zip(titles, pmids)])}\n\n
            Mention sources and the links explicitly at the end.
            If the context does not contain the answer to the question, write 'The suggested context does not contain the answer to the question', and try to answer on your own, giving references to the sources you used. But do not make up anything—use only factual and trustworthy data.
        """

        start = time.time()
        # model_name = 'llama3.2:3b'
        model_name = 'alibayram/medgemma'
        response: ChatResponse = chat(model=model_name, messages=[
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
        logger.info(f"LLM response generation took {time.time() - start:.2f} seconds")
        logger.info(f"Total time for generate_response: {time.time() - start_total:.2f} seconds")
        return response.message.content
    
    def extract_documents(self, query: str):
        #vector search
        results_vector, scores_vector  = self.vector_database.search(query, k=self.k)
        #keyword search
        results_keyword, scores_keyword = self.keyword_database.search(query, k=self.k)

        #reranking
        results_combined = results_vector + results_keyword
        print(len(results_combined))
        reranked_results, reranked_scores = rerank_documents(query, retrieved_results=results_combined, model=self.embedding_model, top_k=self.k)

        return reranked_results, reranked_scores
    
    def generate_wiki_response(self, query: str):
        #vector search
        results_vector, scores_vector  = self.vector_database.search(query, k=self.k)

        #keyword search
        results_keyword, scores_keyword = self.keyword_database.search(query, k=self.k)

        #reranking
        results_combined = results_vector + results_keyword
        reranked_results, reranked_scores = rerank_documents(query, retrieved_results=results_combined, model=self.embedding_model, top_k=self.k)

        # summarize texts
        summarized_texts, pmids, titles = self.summarizer.process(query, reranked_records=reranked_results)

        prompt = f"""
        Question: {query}\n\n
        Context to use to generate a Wiki-article divided into paragraphs and generated lists:\n\n
        {summarized_texts}. If the context does not contain the answer to the question write 'The suggested context does not contain the answer to the question', and try to answer on your own, giving the references to the sources you used. But do not make up anything, use just factual and trustworthy data.
        """

        # model_name = 'llama3.2:3b'
        model_name = 'alibayram/medgemma'
        response: ChatResponse = chat(model=model_name, messages=[
            {
                "role": "system", 
                "content": """
                    You are an expert in producing Wiki-articles based on given content.    
                """
            },
            {
                "role": "user",
                "content": prompt
            },
        ])

        return response.message.content
