import os
import chromadb
from sentence_transformers import SentenceTransformer

class LocalRuBertEmbeddingFunction(chromadb.EmbeddingFunction):
    def __init__(self):
        self.model = SentenceTransformer('cointegrated/rubert-tiny2')

    def __call__(self, input: chromadb.Documents) -> chromadb.Embeddings:
        embeddings = self.model.encode(input, convert_to_numpy=True)
        return embeddings.tolist()

class VectorStoreManager:
    def __init__(self, db_path="data/chroma"):
        os.makedirs(db_path, exist_ok=True)
        self.client = chromadb.PersistentClient(path=db_path)
        self.embedding_fn = LocalRuBertEmbeddingFunction()
        
        self.collection = self.client.get_or_create_collection(
            name="user_notes",
            embedding_function=self.embedding_fn
        )

    def save_note(self, user_id: str, note_id: str, text: str):
        self.collection.add(
            documents=[text], 
            metadatas=[{"user_id": str(user_id), "original_text": text}],
            ids=[f"{user_id}_{note_id}"]
        )

    def search_notes(self, user_id: str, query: str, limit=3):
        results = self.collection.query(
            query_texts=[query],
            n_results=limit,
            where={"user_id": str(user_id)}
        )
        return results.get('documents', [[]])[0] if results else []

    def delete_user_notes(self, user_id: str):
        self.collection.delete(where={"user_id": str(user_id)})