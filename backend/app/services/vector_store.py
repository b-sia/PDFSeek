import os
from typing import Dict, Optional, Literal

from langchain.embeddings import HuggingFaceEmbeddings, OpenAIEmbeddings
from langchain.vectorstores import FAISS

from app.core.config import settings


class VectorStore:
    def __init__(self, embedding_type: Literal["huggingface", "openai"] = "huggingface"):
        """Initialize the vector store with the specified embedding type.
        
        Args:
            embedding_type: The type of embeddings to use ("huggingface" or "openai")
        """
        if embedding_type == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is not set in environment variables")
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=settings.OPENAI_API_KEY
            )
        else:
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
        
        self.store_dir = settings.VECTOR_STORE_DIR
        self.stores: Dict[str, FAISS] = {}
        os.makedirs(self.store_dir, exist_ok=True)
        self.embedding_type = embedding_type

    def get_store(self, doc_id: str) -> FAISS:
        """Get or create a vector store for a document."""
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
vector_store = VectorStore(embedding_type=settings.DEFAULT_EMBEDDING_TYPE if hasattr(settings, "DEFAULT_EMBEDDING_TYPE") else "huggingface")

def get_vector_store() -> VectorStore:
    """Get the vector store singleton instance."""
    return vector_store 