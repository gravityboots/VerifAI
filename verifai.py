import os
import re
import requests
from dotenv import load_dotenv
from typing import List, Dict

# Embedding model
from sentence_transformers import SentenceTransformer
import numpy as np

# Latest Chroma vector DB client usage
import chromadb
from chromadb.config import Settings

# Latest Mistral AI client usage
from mistralai import Mistral

# Load environment variables
load_dotenv()

# MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")

# if not MISTRAL_API_KEY:
#     raise ValueError("MISTRAL_API_KEY missing in .env")
# if not GOOGLE_API_KEY:
#     raise ValueError("GOOGLE_API_KEY missing in .env")
# if not NEWSDATA_API_KEY:
#     raise ValueError("NEWSDATA_API_KEY missing in .env")

NEWSDATA_API_KEY="pub_1c96f65150ed4e20bc7e601519415f8e"
GOOGLE_API_KEY="AIzaSyAO8ZEPZbZ3PiHAXRnjdf1KX-5cZIWeCmg"
MISTRAL_API_KEY="G3fIIlh2SkInWxyVqeLvMkilVk1GMpiV"

mistral_model = "mistral-large-latest"

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize persistent local Chroma client
CHROMA_DIR = "./chroma_db_store"
chroma_client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings())
collection = chroma_client.get_or_create_collection(name="misinfo_checker")

########################
# Claim extraction
########################
def extract_claims(text):
    claims = re.split(r'(?<=[.!?])\s+', text.strip())
    return [c.strip() for c in claims if c.strip()]

def embed_texts(texts):
    return embedding_model.encode(texts, show_progress_bar=False)

########################
# API query functions
########################
def query_google_factcheck(claim):
    url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
    params = {"query": claim, "key": GOOGLE_API_KEY, "languageCode": "en", "pageSize": 5}
    resp = requests.get(url, params=params)
    output = []
    if resp.status_code == 200:
        data = resp.json()
        for fc in data.get("claims", []):
            text = fc.get("text", "")
            if not text:
                for review in fc.get("claimReview", []):
                    rating = review.get("textualRating", "")
                    if rating:
                        text = rating
            if text:
                output.append(f"FactCheck: {text}")
    return output

def query_wikidata(claim):
    query = f"""
    SELECT ?item ?itemLabel ?description WHERE {{
      ?item ?label "{claim}"@en.
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }} LIMIT 5
    """
    url = "https://query.wikidata.org/sparql"
    headers = {"Accept": "application/sparql-results+json"}
    resp = requests.get(url, params={"query": query}, headers=headers)
    results = []
    if resp.status_code == 200:
        for item in resp.json()["results"]["bindings"]:
            label = item.get("itemLabel", {}).get("value", "")
            desc = item.get("description", {}).get("value", "")
            results.append(f"Wikidata: {label}: {desc}")
    return results

def query_newsdata(claim):
    url = "https://newsdata.io/api/1/news"
    params = {"apikey": NEWSDATA_API_KEY, "q": claim, "language": "en", "page": 1, "country": "us"}
    resp = requests.get(url, params=params)
    results = []
    if resp.status_code == 200:
        data = resp.json()
        for article in data.get("results", []):
            title = article.get("title", "")
            description = article.get("description", "")
            if title and description:
                results.append(f"News: {title} - {description}")
    return results

########################
# Vector DB management
########################
def index_documents(text_docs):
    if not text_docs:
        return
    doc_vectors = embed_texts(text_docs)
    ids = [f"doc_{i}" for i in range(len(text_docs))]
    try:
        existing_ids = set(collection.get(ids=ids)["ids"])
        new_ids = [i for i in ids if i not in existing_ids]
        new_docs = [text_docs[i] for i in range(len(text_docs)) if ids[i] in new_ids]
        new_vecs = [doc_vectors[i].tolist() for i in range(len(text_docs)) if ids[i] in new_ids]
        if new_ids:
            collection.add(ids=new_ids, documents=new_docs, embeddings=new_vecs)
    except Exception:
        if 'existing_ids' in locals() and existing_ids:
            collection.delete(ids=list(existing_ids))
        collection.add(ids=ids, documents=text_docs, embeddings=doc_vectors.tolist())

def retrieve_similar_docs(query: str, top_k=5) -> List[str]:
    query_vec = embed_texts([query])[0]
    results = collection.query(query_embeddings=[query_vec.tolist()], n_results=top_k)
    return results.get("documents", [[]])[0]

########################
# Mistral chat interaction
########################
def mistral_chat_generate(prompt):
    with Mistral(api_key=MISTRAL_API_KEY) as mistral:
        response = mistral.chat.complete(
            model=mistral_model,
            messages=[{"role": "user", "content": prompt}],
            stream=False,
            max_tokens=512,
            temperature=0.3,
        )
        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content.strip()
        return "No response from model."

########################
# Main misinformation check pipeline
########################
def misinformation_check(input_text):
    claims = extract_claims(input_text)
    gathered_docs = []
    for claim in claims:
        gathered_docs.extend(query_google_factcheck(claim))
        gathered_docs.extend(query_wikidata(claim))
        gathered_docs.extend(query_newsdata(claim))
    index_documents(gathered_docs)
    context_docs = []
    for claim in claims:
        context_docs.extend(retrieve_similar_docs(claim, top_k=3))

    combined_context = "\n\n".join(context_docs)
    prompt = f"""You are an AI fact-checker. Analyze the following claims along with the evidence provided.

Claims:
{input_text}

Evidence from fact checks, Wikidata, and news:
{combined_context}

For each claim, provide:
- Verdict (True, False, Misleading, Insufficient Data)
- Brief summary explanation
- Identify the key claims clearly

Format your answer with headings "Verdict:", "Summary:", and "Identified Claims:".
"""

    response = mistral_chat_generate(prompt)
    return {
        "verdict_summary": response,
        "identified_claims": claims
    }

########################
# Example usage
########################
if __name__ == "__main__":
    test_input = (
        "The COVID-19 vaccine contains microchips for tracking. "
        "Global warming is a hoax caused by sunspots. "
        "The Eiffel Tower is the tallest building in the world."
    )
    result = misinformation_check(test_input)
    print("=== Identified Claims ===")
    for c in result["identified_claims"]:
        print(f"- {c}")
    print("\n=== Verdict and Summary ===")
    print(result["verdict_summary"])
