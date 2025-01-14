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