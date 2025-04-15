import os
from typing import Dict, Optional, Literal, List
from functools import lru_cache

from langchain.embeddings import HuggingFaceEmbeddings, OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document

from app.core.config import settings


class VectorStore:
    def __init__(self, model_service, embedding_type: Literal["huggingface", "openai"] = "huggingface"):
        """Initialize the vector store with the specified embedding type.
        
        Args:
            model_service: The model service instance to use for configuration
            embedding_type: The type of embeddings to use ("huggingface" or "openai")
        """
        self.store_dir = settings.VECTOR_STORE_DIR
        self.stores: Dict[str, FAISS] = {}
        os.makedirs(self.store_dir, exist_ok=True)
        self.embedding_type = embedding_type
        self.model_service = model_service
        self.embeddings = self._create_embeddings(embedding_type)

    @lru_cache(maxsize=2)
    def _create_embeddings(self, embedding_type: str):
        """Create embedding model based on the specified type"""
        if embedding_type == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is not set in environment variables")
            return OpenAIEmbeddings(
                openai_api_key=settings.OPENAI_API_KEY
            )
        else:
            return HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={"trust_remote_code": True}
            )
            
    def update_embeddings(self, embedding_type: str):
        """Update the embedding model if the type has changed"""
        if settings.DEBUG:
            print(f"update_embeddings called with type: {embedding_type}, current type: {self.embedding_type}")
        
        # Compare embedding types after stripping whitespace
        new_type = str(embedding_type).strip()
        current_type = str(self.embedding_type).strip()
        
        if new_type != current_type:
            if settings.DEBUG:
                print(f"Updating embeddings from {current_type} to {new_type}")
            
            # Create new embeddings
            self.embeddings = self._create_embeddings(new_type)
            self.embedding_type = new_type
            
            # Clear all stores since we're changing embedding types
            self.stores = {}
            
            if settings.DEBUG:
                print(f"Embeddings updated successfully to {new_type}")
        else:
            if settings.DEBUG:
                print(f"No update needed, already using {new_type} embeddings")

    def get_store(self, doc_id: str) -> FAISS:
        """Get or create a vector store for a document."""
        # Get current embedding type from model service configuration
        config_embedding_type = self.model_service.get_config().get("embedding_type")
        
        # Update embeddings if necessary
        if config_embedding_type != self.embedding_type:
            self.update_embeddings(config_embedding_type)
            
        if doc_id not in self.stores:
            store_path = os.path.join(self.store_dir, f"{doc_id}.faiss")
            if os.path.exists(store_path):
                self.stores[doc_id] = FAISS.load_local(
                    store_path,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
            else:
                # Initialize with a dummy document to create the store
                self.stores[doc_id] = FAISS.from_texts(
                    ["Initial document"],  # Use a non-empty text
                    self.embeddings
                )
        return self.stores[doc_id]

    def add_document(self, doc_id: str, text: str) -> None:
        """Add a document to the vector store."""
        if not text or not text.strip():
            if settings.DEBUG:
                print(f"Skipping empty text for document {doc_id}")
            return
            
        try:
            store = self.get_store(doc_id)
            
            # Create a Document object with metadata
            doc = Document(
                page_content=text,
                metadata={"doc_id": doc_id}
            )
            
            # Add the document to the store
            store.add_documents([doc])
            
            # Save the updated store
            store.save_local(os.path.join(self.store_dir, f"{doc_id}.faiss"))
            
            if settings.DEBUG:
                print(f"Successfully added document {doc_id} to vector store")
        except Exception as e:
            if settings.DEBUG:
                print(f"Error adding document {doc_id} to vector store: {str(e)}")
            raise

    def add_texts(self, doc_id: str, texts: List[str]) -> None:
        """Add multiple text chunks to the vector store.
        
        Args:
            doc_id: The document ID
            texts: List of text chunks to add
        """
        if not texts:
            if settings.DEBUG:
                print(f"No texts provided for document {doc_id}")
            return
            
        try:
            # Filter out empty texts
            valid_texts = [text for text in texts if text and text.strip()]
            
            if not valid_texts:
                if settings.DEBUG:
                    print(f"No valid texts found for document {doc_id}")
                return
                
            store = self.get_store(doc_id)

            docs = [
                Document(
                    page_content=text,
                    metadata={"doc_id": doc_id, "chunk_index": i}
                )
                for i, text in enumerate(valid_texts)
            ]
            
            store.add_documents(docs)
            
            # Save the updated store
            store.save_local(os.path.join(self.store_dir, f"{doc_id}.faiss"))
            
            if settings.DEBUG:
                print(f"Successfully added {len(docs)} chunks to document {doc_id}")
        except Exception as e:
            if settings.DEBUG:
                print(f"Error adding texts to document {doc_id}: {str(e)}")
            raise

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


vector_store = None

def get_vector_store(model_service=None) -> VectorStore:
    """Get the vector store singleton instance."""
    global vector_store
    if vector_store is None:
        if model_service is None:
            raise ValueError("model_service must be provided when initializing vector_store")
        vector_store = VectorStore(model_service, embedding_type=settings.DEFAULT_EMBEDDING_TYPE)
    return vector_store 