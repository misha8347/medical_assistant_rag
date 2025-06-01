from flask import Flask, render_template, jsonify, request
import torch
from langchain_huggingface import HuggingFaceEmbeddings
from deep_translator import GoogleTranslator
from langdetect import detect
from loguru import logger


import sys
import os

parent_folder = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
sys.path.append(parent_folder)

#local imports
# from medrag.pipeline.qa_base_pipeline import QABasePipeline
from medrag.pipeline.qa_pipeline import QAPipeline
from medrag.retrieval.reranking import rerank_documents
from medrag.retrieval.keyword_db import KeywordDB
from medrag.retrieval.vector_db import VectorDB
from medrag.summarization.summarization import QueryBasedTextRankSummarizer

# ML
# qa_base_pipeline = QABasePipeline()
query_based_summarizer = QueryBasedTextRankSummarizer()
keyword_database = KeywordDB()
vector_database = VectorDB()

keyword_database.load_db()
vector_database.load_db()

device = torch.device('cpu')
model = HuggingFaceEmbeddings(model_name="neuml/pubmedbert-base-embeddings", 
                                        model_kwargs={'device': device},
                                        encode_kwargs={"normalize_embeddings": True})

qa_pipeline = QAPipeline(vector_database, keyword_database, query_based_summarizer, embedding_model=model)


#Backend
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('chat.html')

@app.route('/generate_health_recommendation', methods=['POST'])
def generate_health_recommendation():
    logger.info('received query from user!')
    try:
        data = request.get_json()  # Get JSON request
        question = data.get("query")

        translator = GoogleTranslator(source='auto', target='en')
        translated_text = translator.translate(question)
        detected_lang = detect(question)

        if not question:
            return jsonify({"error": "No question provided"}), 400

        response = qa_pipeline.generate_response(translated_text)
        translator = GoogleTranslator(source='en', target=detected_lang)
        translated_response = translator.translate(response)
        logger.info('sending response back to user!')
        return jsonify({"response": translated_response})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000, debug=True)