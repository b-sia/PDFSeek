import os
from typing import Dict, Optional, Literal
from functools import lru_cache

from langchain.embeddings import HuggingFaceEmbeddings, OpenAIEmbeddings
from langchain.vectorstores import FAISS

from app.core.config import settings
from app.services.model_service import model_service


class VectorStore:
    def __init__(self, embedding_type: Literal["huggingface", "openai"] = "huggingface"):
        """Initialize the vector store with the specified embedding type.
        
        Args:
            embedding_type: The type of embeddings to use ("huggingface" or "openai")
        """
        self.store_dir = settings.VECTOR_STORE_DIR
        self.stores: Dict[str, FAISS] = {}
        os.makedirs(self.store_dir, exist_ok=True)
        self.embedding_type = embedding_type
        self.embeddings = self._create_embeddings(embedding_type)

    @lru_cache(maxsize=2)
    def _create_embeddings(self, embedding_type: str):
        """Create embedding model based on the specified type with caching"""
        if embedding_type == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is not set in environment variables")
            return OpenAIEmbeddings(
                openai_api_key=settings.OPENAI_API_KEY
            )
        else:
            return HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            
    def update_embeddings(self, embedding_type: str):
        """Update the embedding model if the type has changed"""
        print(f"update_embeddings called with type: {embedding_type}, current type: {self.embedding_type}")
        print(f"Embedding type type: {type(embedding_type)}, current type type: {type(self.embedding_type)}")
        if str(embedding_type).strip() != str(self.embedding_type).strip():
            print(f"Updating embeddings from {self.embedding_type} to {embedding_type}")
            self.embeddings = self._create_embeddings(embedding_type)
            self.embedding_type = embedding_type
            # Only clear stores if we're actually changing embedding types
            if self.embedding_type != embedding_type:
                self.stores = {}
            print(f"Embeddings updated successfully to {embedding_type}")
        else:
            print(f"No update needed, already using {embedding_type} embeddings")

    def get_store(self, doc_id: str) -> FAISS:
        """Get or create a vector store for a document."""
        # Get current embedding type from model service configuration
        config_embedding_type = model_service.get_config().get("embedding_type")
        
        # Update embeddings if necessary
        if config_embedding_type != self.embedding_type:
            self.update_embeddings(config_embedding_type)
            
        if doc_id not in self.stores:
            store_path = os.path.join(self.store_dir, f"{doc_id}.faiss")
            if os.path.exists(store_path):
                self.stores[doc_id] = FAISS.load_local(
                    store_path,
                    self.embeddings
                )
            else:
                self.stores[doc_id] = FAISS.from_texts(
                    [""],  # Initialize with empty text
                    self.embeddings
                )
        return self.stores[doc_id]

    def add_document(self, doc_id: str, text: str) -> None:
        """Add a document to the vector store."""
        store = self.get_store(doc_id)
        store.add_texts([text])
        store.save_local(os.path.join(self.store_dir, f"{doc_id}.faiss"))

    def get_document(self, doc_id: str) -> Optional[str]:
        """Get a document from the vector store."""
        store = self.get_store(doc_id)
        if store:
            # Get the first document (assuming one document per store)
            docs = store.similarity_search("", k=1)
            return docs[0].page_content if docs else None
        return None

    def delete_document(self, doc_id: str) -> None:
        """Delete a document from the vector store."""
        store_path = os.path.join(self.store_dir, f"{doc_id}.faiss")
        if os.path.exists(store_path):
            os.remove(store_path)
        if doc_id in self.stores:
            del self.stores[doc_id]

# Create singleton instance with default embedding type
vector_store = VectorStore(embedding_type=settings.DEFAULT_EMBEDDING_TYPE)

def get_vector_store() -> VectorStore:
    """Get the vector store singleton instance."""
    return vector_store 