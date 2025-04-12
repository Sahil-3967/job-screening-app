from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Load once and reuse
model = SentenceTransformer("all-MiniLM-L6-v2")

def get_embedding(text):
    return model.encode(text)

def calculate_match(jd_summary, resume_text):
    vec1 = get_embedding(jd_summary)
    vec2 = get_embedding(resume_text)
    similarity = cosine_similarity([vec1], [vec2])[0][0]
    return round(similarity * 100, 2)
