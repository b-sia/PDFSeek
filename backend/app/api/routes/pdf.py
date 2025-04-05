from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from app.services.pdf_service import process_pdfs
from app.models.pdf import PDFResponse

router = APIRouter()

@router.post("/upload", response_model=PDFResponse)
async def upload_pdfs(files: List[UploadFile] = File(...)):
    """
    Upload and process multiple PDF files.
    Returns the status of processing and document IDs.
    """
    try:
        result = await process_pdfs(files)
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
