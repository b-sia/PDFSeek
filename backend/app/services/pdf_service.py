import os
import uuid
from typing import Dict, List

from fastapi import UploadFile
from PyPDF2 import PdfReader

from app.core.config import settings
from app.services.vector_store import get_vector_store


async def process_pdfs(files: List[UploadFile]) -> Dict[str, any]:
    """
    Process uploaded PDF files and store them in the vector store.
    Returns document IDs and total page count.
    """
    vector_store = get_vector_store()
    document_ids = []
    total_pages = 0

    for file in files:
        try:
            # Generate unique document ID
            doc_id = str(uuid.uuid4())
            
            # Read PDF content
            pdf_reader = PdfReader(file.file)
            total_pages += len(pdf_reader.pages)

            # Process each page
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text.strip():
                    # Add to vector store
                    vector_store.add_document(doc_id, text)

            document_ids.append(doc_id)
            file.file.close()

        except Exception as e:
            # Clean up on error
            if doc_id in document_ids:
                vector_store.delete_document(doc_id)
            raise Exception(f"Error processing PDF {file.filename}: {str(e)}")

    return {
        "document_ids": document_ids,
        "total_pages": total_pages
    } 