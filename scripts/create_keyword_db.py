import os
import json
import bm25s
import Stemmer
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class KeywordDB:
    def __init__(self, db_path: str = '/s3/misha/data_dir/PMC_patients/db_bm25s'):
        self.db_path = db_path
        self.stemmer = Stemmer.Stemmer("english")
        self.retriever = None
        # self.index_to_metadata = {}
    
    def create_knowledge_base(self, df: pd.DataFrame):
        logger.info('Sampling 100k chunks...')
        df = df.sample(n=100000, random_state=42)
        
        logger.info('Tokenizing chunks...')
        corpus = df[['chunk', 'PMID', 'title']].to_dict(orient='records')
        corpus_texts = [doc['chunk'] for doc in corpus]

        corpus_tokens = bm25s.tokenize(corpus_texts, stopwords="en", stemmer=self.stemmer)
        self.retriever = bm25s.BM25()
        self.retriever.index(corpus_tokens)
        
        os.makedirs(self.db_path, exist_ok=True)
        self.retriever.save(self.db_path, corpus=corpus_texts)
        
        with open(f'{self.db_path}/corpus.jsonl', 'w') as f:
            for record in corpus:
                f.write(json.dumps(record) + '\n')
        
        logger.info('Knowledge base created successfully!')
    
    def load_db(self):
        if not os.path.exists(self.db_path):
            raise ValueError("Keyword database file not found. Use create_knowledge_base to create a new database.")
        
        self.retriever = bm25s.BM25.load(self.db_path, load_corpus=True)
        with open(f'{self.db_path}/corpus.jsonl', 'r') as f:
            self.bm25s_corpus = [json.loads(line) for line in f]
        
        # self.index_to_metadata = {i: doc for i, doc in enumerate(self.bm25s_corpus)}
        logger.info('keyword database loaded successfully!')
    
    def search(self, query: str, k: int):
        if self.retriever is None:
            raise ValueError("Keyword database is not loaded. Use load_db() to load the database.")
        
        query_tokens = bm25s.tokenize(query, stemmer=self.stemmer)
        results, scores = self.retriever.retrieve(query_tokens, k=k)
        results = results[0].tolist()
        scores = scores[0].tolist()
        
        return results, scores


def main():
    import pandas as pd
    df_pmc_patients = pd.read_parquet('/s3/misha/data_dir/PMC_patients/chunked_texts.parquet', engine='pyarrow')

    keyword_database = KeywordDB()
    keyword_database.create_knowledge_base(df_pmc_patients)

if __name__ == "__main__":
    main()