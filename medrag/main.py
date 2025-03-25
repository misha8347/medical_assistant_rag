from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from deep_translator import GoogleTranslator
from langdetect import detect
import torch
from langchain_huggingface import HuggingFaceEmbeddings



#local imports

# from pipeline.qa_base_pipeline import QABasePipeline
from pipeline.qa_pipeline import QAPipeline
from retrieval.reranking import rerank_documents
from retrieval.keyword_db import KeywordDB
from retrieval.vector_db import VectorDB
from summarization.summarization import QueryBasedTextRankSummarizer


class HealthRequest(BaseModel):
    query: str

# ML

# qa_base_pipeline = QABasePipeline()
query_based_summarizer = QueryBasedTextRankSummarizer()
keyword_database = KeywordDB()
vector_database = VectorDB()

keyword_database.load_db()
vector_database.load_db()

device = torch.device('cuda:0')
model = HuggingFaceEmbeddings(model_name="neuml/pubmedbert-base-embeddings", 
                                        model_kwargs={'device': device},
                                        encode_kwargs={"normalize_embeddings": True})

qa_pipeline = QAPipeline(vector_database, keyword_database, query_based_summarizer, embedding_model=model)

# Backend
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/generate_health_recommendation/")
async def generate_health_recommendation(request: HealthRequest):
    try:
        translator = GoogleTranslator(source='auto', target='en')
        translated_text = translator.translate(request.query)
        detected_lang = detect(request.query)
        
        # response = qa_base_pipeline.generate_response(translated_text)
        response = qa_pipeline.generate_response(translated_text)
        translator = GoogleTranslator(source='en', target=detected_lang)
        translated_response = translator.translate(response)
        return {'response': translated_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")