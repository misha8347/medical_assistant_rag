from sentence_transformers import SentenceTransformer, util
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer
from sumy.parsers.plaintext import PlaintextParser
import torch
from typing import List


class QueryBasedTextRankSummarizer:
    def __init__(self):
        self.embedding_model = SentenceTransformer('neuml/pubmedbert-base-embeddings')
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.embedding_model.to(self.device)

    def process(self, query: str, reranked_records: List[dict]):
        context_snippets = [record['chunk'] for record in reranked_records if record['chunk'].strip()]
        pmids = [record['PMID'] for record in reranked_records]
        titles = [record['title'] for record in reranked_records]
        if not context_snippets:
            raise ValueError("context_snippets must be a non-empty list of valid sentences.")

        query_embedding = self.embedding_model.encode(query, convert_to_tensor=True).to(self.device)
        sentence_embeddings = self.embedding_model.encode(context_snippets, convert_to_tensor=True).to(self.device)

        similarities = util.cos_sim(query_embedding, sentence_embeddings).squeeze().tolist()

        ranked_sentences = sorted(
            zip(similarities, context_snippets), reverse=True, key=lambda x: x[0]
        )

        count_ranked_sentences = len(ranked_sentences)
        filtered_context = " ".join([sentence for _, sentence in ranked_sentences[:int(count_ranked_sentences / 2)]])

        summary_sentence_count = max(1, round(0.2 * count_ranked_sentences))
        parser = PlaintextParser.from_string(filtered_context, Tokenizer("english"))
        summarizer = TextRankSummarizer()
        summary = summarizer(parser.document, summary_sentence_count)

        summarized_text = ''.join(sentence._text for sentence in summary)
        return summarized_text, pmids, titles
