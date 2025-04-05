from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.models.pdf import PDFResponse
from app.services.pdf_service import process_pdfs
from app.services.session_service import session_service

router = APIRouter()

# Dependency to get session
async def get_session():
    session_id = session_service.create_session()
    return session_id

@router.post("/upload", response_model=PDFResponse)
async def upload_pdfs(
    files: List[UploadFile] = File(...),
    session_id: str = Depends(get_session)
):
    """
    Upload and process multiple PDF files.
    Returns the status of processing and document IDs.
    """
    try:
        result = await process_pdfs(files)
        for doc_id in result["document_ids"]:
            session_service.add_document_to_session(session_id, doc_id)
        return PDFResponse(
            success=True,
            message="PDFs processed successfully",
            document_ids=result["document_ids"],
            total_pages=result["total_pages"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing PDFs: {str(e)}"
        )
