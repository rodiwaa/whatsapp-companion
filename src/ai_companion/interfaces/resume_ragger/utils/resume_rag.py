# utils/resume_rag.py
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

class ResumeRAG:
    def __init__(self):
        self.client = QdrantClient("localhost", port=6333)
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.collection_name = "resume_collection"
    
    def setup_collection(self):
        # Create collection if it doesn't exist
        try:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
        except Exception:
            pass  # Collection already exists
    
    def add_resume_chunks(self, resume_text_chunks):
        # Add your resume content to the collection
        points = []
        for i, chunk in enumerate(resume_text_chunks):
            vector = self.encoder.encode(chunk).tolist()
            points.append(PointStruct(
                id=i,
                vector=vector,
                payload={"text": chunk, "source": "resume"}
            ))
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
    
    def search_resume(self, query, limit=3):
        query_vector = self.encoder.encode(query).tolist()
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit
        )
        return [hit.payload["text"] for hit in search_result]
