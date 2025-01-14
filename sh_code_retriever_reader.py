import torch
from sentence_transformers import SentenceTransformer
import numpy as np
from transformers import (AutoModelForQuestionAnswering, AutoTokenizer, pipeline)

retriever_model = SentenceTransformer('all-MiniLM-L6-v2')
model_name = "sjrhuschlee/flan-t5-base-squad2"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
nlp = pipeline(
        'question-answering',
        model=model_name,
        tokenizer=model_name,
        # trust_remote_code=True, # Do not use if version transformers>=4.31.0
    )

def chunk_text(text, chunk_size=300):
    words = text.split()
    chunks = [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
    return chunks


def retrieve_chunks(question, chunks, top_n=3):
    question_embedding = retriever_model.encode([question])
    chunk_embeddings = retriever_model.encode(chunks)
    # similarities = cosine_similarity(question_embedding, chunk_embeddings).flatten()
    similarities = np.dot(question_embedding, chunk_embeddings.T).flatten()
    top_chunk_indices = np.argsort(similarities)[-top_n:][::-1]
    top_chunks = [chunks[i] for i in top_chunk_indices]
    return top_chunks