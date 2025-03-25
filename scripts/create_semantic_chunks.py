import pandas as pd
from loguru import logger
from tqdm import tqdm
import torch
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_experimental.text_splitter import SemanticChunker


def main(df: pd.DataFrame, save_path: str):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(device)
    embeddings_model = HuggingFaceEmbeddings(model_name="neuml/pubmedbert-base-embeddings", 
                                                model_kwargs={'device': device},
                                                encode_kwargs={"normalize_embeddings": True})
    text_splitter = SemanticChunker(embeddings_model)

    logger.info('Chunking texts using Semantic embeddings...')
    df_unique_texts = df.drop_duplicates(subset='full_text')
    splitting_texts_with_progress = tqdm(df_unique_texts.iterrows(), desc="Splitting texts using SemanticChunker", total=len(df_unique_texts))
    
    records = []
    for index, value in splitting_texts_with_progress:
        semantic_chunks = text_splitter.create_documents([value['full_text']])
        semantic_chunks = [chunk.page_content for chunk in semantic_chunks]
        
        for chunk in semantic_chunks:
            record = {
                    'PMID': value['PMID'],
                    'title': value['title'],
                    'chunk': chunk
                }
            records.append(record)

    logger.info('saving chunks to pd dataframe')
    df_to_save = pd.DataFrame(records)
    df_to_save.to_parquet(save_path, engine='pyarrow', compression='snappy')


if __name__ == "__main__":
    df_pmc_patients = pd.read_parquet('/s3/misha/data_dir/PMC_patients/full_texts_PMC-Patients-V2.parquet', engine='pyarrow')
    # df_pmc_patients = df_pmc_patients.sample(n=10)
    save_path = '/s3/misha/data_dir/PMC_patients/chunked_texts.parquet'
    main(df=df_pmc_patients, save_path=save_path)