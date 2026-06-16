import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from transformers import pipeline
from duckduckgo_search import DDGS

class RAGPipeline:
    def __init__(self):
        print("Initializing RAG Pipeline...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        # Using a small NLI model to determine entailment (true/false)
        self.nli_model = pipeline("zero-shot-classification", model="cross-encoder/nli-deberta-v3-small")
        
        self.dimension = self.embedding_model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents = []
        
        # Load a dummy knowledge base for demonstration
        self._load_dummy_knowledge_base()
        print("RAG Pipeline Ready.")

    def _load_dummy_knowledge_base(self):
        initial_facts = [
            "The Earth revolves around the Sun.",
            "Water boils at 100 degrees Celsius at sea level.",
            "Vaccines are proven to be safe and effective by the CDC.",
            "The capital of France is Paris."
        ]
        self.add_documents(initial_facts)

    def add_documents(self, docs: list[str]):
        if not docs: return
        embeddings = self.embedding_model.encode(docs)
        self.index.add(np.array(embeddings).astype('float32'))
        self.documents.extend(docs)

    def search_local(self, query: str, k: int = 1) -> str:
        if self.index.ntotal == 0:
            return ""
        query_vector = self.embedding_model.encode([query])
        distances, indices = self.index.search(np.array(query_vector).astype('float32'), k)
        
        # If distance is too high (not a good match), return empty
        if distances[0][0] > 1.5:  # Arbitrary threshold for L2 distance
            return ""
        
        best_match_idx = indices[0][0]
        return self.documents[best_match_idx]

    def search_web(self, query: str) -> str:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=2))
                if results:
                    # Combine snippets as evidence
                    return " ".join([res['body'] for res in results])
        except Exception as e:
            print(f"DuckDuckGo API error: {e}")
        return ""

    def get_verdict(self, claim: str, evidence: str) -> dict:
        if not evidence:
            return {"verdict": "unverified", "confidence": 0.0}
            
        candidate_labels = ["true", "false", "unverified"]
        
        # Using zero-shot cross-encoder format for entailment
        combined_text = f"Evidence: {evidence} Claim: {claim}"
        result = self.nli_model(combined_text, candidate_labels)
        
        best_label = result['labels'][0]
        confidence = result['scores'][0]
        
        return {"verdict": best_label, "confidence": round(confidence, 4)}

    def factcheck(self, claim: str) -> dict:
        # 1. Try local vector DB first
        evidence = self.search_local(claim)
        
        # 2. If no local evidence, fallback to Web Search
        if not evidence:
            evidence = self.search_web(claim)
            if evidence:
                # Cache the new evidence
                self.add_documents([evidence])
                
        if not evidence:
            return {
                "verdict": "unverified",
                "evidence": "No relevant evidence found in local KB or web.",
                "confidence": 0.0
            }
            
        # 3. Analyze claim against evidence
        verdict_data = self.get_verdict(claim, evidence)
        
        return {
            "verdict": verdict_data["verdict"],
            "evidence": evidence,
            "confidence": verdict_data["confidence"]
        }
