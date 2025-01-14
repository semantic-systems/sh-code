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


# Reader to find the answer from the selected chunks
def run_retriever_reader(question, text, chunk_size=200, top_n=3 ):
    chunks = chunk_text(text, chunk_size)
    relevant_chunks = retrieve_chunks(question, chunks, top_n)
    top_n_answers = []
    for chunk in relevant_chunks:
        qa_input = {
            'question': f"{nlp.tokenizer.cls_token}{question}",  # '<cls>Where do I live?'
            'context': chunk
        }
        res = nlp(qa_input)
        res.update({"context_chunk": chunk})
        top_n_answers.append(res)
    final_answer = max(top_n_answers, key=lambda x: x['score'])
    best_answer = final_answer["answer"].strip()
    best_answer = best_answer.strip(")")
    best_answer = best_answer.strip("(")
    best_answer = best_answer.strip(".")
    best_answer = best_answer.rstrip(",")
    best_answer = best_answer.rstrip("),")
    return best_answer, top_n_answers


if __name__ == "__main__":
    # Example usage
    text = "Eric 'Rick' C. R. Hehner (born 16 September 1947) is a Canadian computer scientist. He was born in Ottawa. He studied mathematics and physics at Carleton University, graduating with a Bachelor of Science (B.Sc.) in 1969. He studied computer science at the University of Toronto, graduating with a Master of Science (M.Sc.) in 1970, and a Doctor of Philosophy (Ph.D.) in 1974. He then joined the faculty there, becoming a full professor in 1983. He became the Bell University Chair in software engineering in 2001, and retired in 2012."
    question = "What is the birth date of  Eric Hehner ?"
    text = text.strip()
    answer, top_n_answers = run_retriever_reader(question, text, chunk_size=200, top_n=3)
    print("Answer:", answer)
    print("All Answer:", top_n_answers)