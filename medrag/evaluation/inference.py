import sys
import os
import torch
import json
from langchain_huggingface import HuggingFaceEmbeddings
import argparse
import pandas as pd
from loguru import logger
from tqdm import tqdm

parent_folder = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
sys.path.append(parent_folder)
print(parent_folder)

grandparent_dir = os.path.dirname(parent_folder)
sys.path.append(grandparent_dir)

#local imports
# from pipeline.qa_base_pipeline import QABasePipeline
from pipeline.qa_pipeline import QAPipeline
from retrieval.reranking import rerank_documents
from retrieval.keyword_db import KeywordDB
from retrieval.vector_db import VectorDB
from summarization.summarization import QueryBasedTextRankSummarizer


def main():
    # ML
    # qa_base_pipeline = QABasePipeline()
    query_based_summarizer = QueryBasedTextRankSummarizer()
    keyword_database = KeywordDB(db_path='/s3/misha/data_dir/PMC_patients/db_bm25s_ppr')
    vector_database = VectorDB(db_path='/s3/misha/data_dir/PMC_patients/db_faiss_ppr')

    keyword_database.load_db()
    vector_database.load_db()

    device = torch.device('cuda:0')
    model = HuggingFaceEmbeddings(model_name="neuml/pubmedbert-base-embeddings", 
                                            model_kwargs={'device': device},
                                            encode_kwargs={"normalize_embeddings": True})

    qa_pipeline = QAPipeline(vector_database, keyword_database, query_based_summarizer, embedding_model=model, k=200)
    logger.info('loaded all artifacts!')
    # parse args
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--task",
        choices = ["PPR", "PAR"],
        type = str,
        required = True,
        help = "Which task to evaluate, PAR or PPR."
    )
    parser.add_argument(
        "--split",
        choices = ["train", "dev", "test"],
        type = str,
        required = True,
        help = "Which split to evaluate, train, dev, or test."
    )
    parser.add_argument(
        "--result_path",
        type = str,
        required = True,
        help = "The path to store results to be evaluated."
    )
    args = parser.parse_args()

    corpus_path = f"./datasets/{args.task}/{args.task}_corpus.jsonl"
    query_path = f"./datasets/queries/{args.split}_queries.jsonl"
    qrels_path = f"./datasets/{args.task}/{args.task}_{args.split}_qrels.tsv"

    result_folder = os.path.dirname(args.result_path)
    os.makedirs(result_folder, exist_ok=True)
    records = {}
    df_queries = pd.read_json(query_path, lines=True)
    for index, value in tqdm(df_queries.iterrows(), total=len(df_queries)):
        reranked_results, reranked_scores = qa_pipeline.extract_documents(query=value['text'])
        record_dict = {}
        for i, (result, score) in enumerate(zip(reranked_results, reranked_scores)):
            pmid = result['PMID']
            record_dict[pmid] = score

        records[value['_id']] = record_dict #my code here
    
    #save json file
    with open(args.result_path, 'w') as json_file:
        json.dump(records, json_file, indent=4)
    logger.info('inference finished')

if __name__ == "__main__":
    main()

