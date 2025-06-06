from langchain_community.vectorstores import FAISS
import faiss
import pandas as pd
from loguru import logger
import os
from langchain_core.documents import Document
import torch
from tqdm import tqdm
from typing import List, Tuple
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.docstore.in_memory import InMemoryDocstore


#https://www.anthropic.com/news/contextual-retrieval
#https://github.com/anthropics/anthropic-cookbook/tree/main/skills/contextual-embeddings

def convert_documents_to_text(results: List[Tuple[Document, float]]) -> str:
    context = "\n\n".join(doc.page_content for doc, score in results)
    return context

class VectorDB:
    def __init__(self, 
                 db_path: str = '/Users/mikhailogay/Documents/MaProjects/medical_assistant_rag/db_faiss'):
        self.db_path = db_path
        os.makedirs(self.db_path, exist_ok=True)

        # self.index_path = os.path.join(self.db_path, "faiss_index.idx")
        self.index_path = '/Users/mikhailogay/Documents/MaProjects/medical_assistant_rag/index.faiss2'
        self.metadata_path = os.path.join(self.db_path, "metadata.pkl")

        self.device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
        self.embeddings_model = HuggingFaceEmbeddings(model_name="neuml/pubmedbert-base-embeddings", 
                                                      model_kwargs={'device': self.device},
                                                      encode_kwargs={"normalize_embeddings": True})

    def create_knowledge_base(self, df: pd.DataFrame, batch_size: int = 1000):
        def document_generator():
            """Генератор документов, чтобы не хранить их в памяти"""
            for _, row in df.iterrows():
                yield Document(
                    page_content=row['chunk'],
                    metadata={'PMID': row['PMID'], 'title': row['title']}
                )

        logger.info('Initializing FAISS index...')
        embedding_dim = len(self.embeddings_model.embed_query("hello world"))
        # index = faiss.IndexFlatIP(embedding_dim)  # Можно заменить на IndexIVFFlat для экономии памяти
        index = faiss.read_index(self.index_path)

        self.vector_store = FAISS(
            embedding_function=self.embeddings_model,
            index=index,
            docstore=InMemoryDocstore(),
            index_to_docstore_id={},
        )

        logger.info('Adding documents to FAISS...')
        buffer = []
        for i, doc in enumerate(tqdm(document_generator(), total=len(df))):
            buffer.append(doc)
            if len(buffer) >= batch_size:
                self.vector_store.add_documents(documents=buffer)
                buffer.clear()  # Очистка списка после загрузки в FAISS

        if buffer:  # Добавляем оставшиеся документы
            self.vector_store.add_documents(documents=buffer)

        logger.info('Saving vector store...')
        self.vector_store.save_local(self.db_path)
        logger.info('Vector store saved successfully!')

    def load_db(self):
        if not os.path.exists(self.db_path):
            raise ValueError("Vector database file not found. Use upload_data to create a new database.")

        self.vector_store = FAISS.load_local(self.db_path, 
                                             embeddings=self.embeddings_model, 
                                             allow_dangerous_deserialization=True)
        logger.info('vector database loaded from the local file successfully!')

    def search(self, query: str, k: int):
        if not self.vector_store:
            raise ValueError("Vector database is not created. Use create_knowledge_base() to create a new database.")
        results = self.vector_store.similarity_search_with_relevance_scores(query, k=k)
        results_rewritten = [{
            'PMID': result[0].metadata['PMID'],
            'title': result[0].metadata['title'],
            'chunk': result[0].page_content,
            # 'score': result[1]
        } for result in results]
        
        scores = [result[1] for result in results]  

        return results_rewritten, scores