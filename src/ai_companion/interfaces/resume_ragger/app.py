from fastapi import APIRouter, UploadFile, File, HTTPException
import logging
import os
from typing import List
import asyncio
from pypdf import PdfReader
import uuid
import hashlib

from ai_companion.modules.memory.resume_rag.vector_store import get_resume_rag_vector_store

logger = logging.getLogger(__name__)

resume_ragger_router = APIRouter()

# Directory to store uploaded PDFs
PDF_STORAGE_DIR = "src/ai_companion/interfaces/resume_ragger/data/.personal"

# File to keep track of embedded PDFs
PDF_TRACKING_FILE = "src/ai_companion/interfaces/resume_ragger/embedded_pdfs.txt"

resume_rag_vector_store = get_resume_rag_vector_store()

def get_embedded_pdfs() -> List[str]:
    """Reads the list of embedded PDF filenames from the tracking file."""
    if not os.path.exists(PDF_TRACKING_FILE):
        return []
    
    with open(PDF_TRACKING_FILE, "r") as f:
        return [line.strip() for line in f if line.strip()]

def add_embedded_pdf(filename: str):
    """Adds a PDF filename to the tracking file."""
    with open(PDF_TRACKING_FILE, "a") as f:
        f.write(filename + "\n")

def generate_point_id(filename: str, chunk_index: int) -> str:
    """Generates a UUID-based point ID for Qdrant."""
    # Create a consistent UUID based on filename and chunk index
    combined_string = f"{filename}_{chunk_index}"
    # Use MD5 hash to create a consistent UUID
    hash_object = hashlib.md5(combined_string.encode())
    # Convert to UUID format
    return str(uuid.UUID(hash_object.hexdigest()))

async def read_pdf(file_path: str) -> str:
    """Reads text content from a PDF file."""
    text = ""
    with open(file_path, "rb") as f:
        reader = PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
    
    print(f'text: {text}')
    return text

async def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """Splits text into chunks with overlap."""
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - chunk_overlap
        
        if chunk_overlap >= chunk_size:
            break
    
    return chunks

@resume_ragger_router.post("/upload_pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Uploads a PDF file to the server and stores it in the data directory.
    """
    try:
        os.makedirs(PDF_STORAGE_DIR, exist_ok=True)
        file_path = os.path.join(PDF_STORAGE_DIR, file.filename)
        
        # Check if file already exists to prevent re-uploading the same file
        if os.path.exists(file_path):
            return {"message": f"File {file.filename} already exists. Skipping upload."}
        
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        logger.info(f"PDF uploaded successfully: {file.filename}")
        logger.info(f"PDF_STORAGE_DIR {PDF_STORAGE_DIR}")
        
        return {"message": f"Successfully uploaded {file.filename}"}
    
    except Exception as e:
        logger.error(f"Error uploading PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload {file.filename}: {e}")

@resume_ragger_router.post("/process_pdfs/")
async def process_pdfs():
    """
    Processes all new PDF files in the data directory, embeds them into Qdrant,
    and updates the tracking file.
    """
    try:
        os.makedirs(PDF_STORAGE_DIR, exist_ok=True)
        all_pdfs_in_data_dir = [f for f in os.listdir(PDF_STORAGE_DIR) if f.endswith(".pdf")]
        logger.info(f"all_pdfs_in_data_dir {all_pdfs_in_data_dir}")
        
        embedded_pdfs = get_embedded_pdfs()
        new_pdfs_to_process = [pdf for pdf in all_pdfs_in_data_dir if pdf not in embedded_pdfs]
        
        logger.info(f"new_pdfs_to_process {new_pdfs_to_process}")
        print(f"new_pdfs_to_process {new_pdfs_to_process}")
        
        if not new_pdfs_to_process:
            return {"message": "No new PDF files to process."}
        
        processed_count = 0
        
        for pdf_filename in new_pdfs_to_process:
            pdf_path = os.path.join(PDF_STORAGE_DIR, pdf_filename)
            logger.info(f"Processing new PDF: {pdf_filename}")
            print(f"Processing new PDF: {pdf_filename}")
            
            # 1. Read PDF content
            pdf_text = await read_pdf(pdf_path)
            
            # 2. Chunk text
            chunks = await chunk_text(pdf_text)
            
            # 3. Store chunks in Qdrant with proper point IDs
            # chunks_with_ids = []
            # for i, chunk in enumerate(chunks):
            #     point_id = generate_point_id(pdf_filename, i)
            #     chunks_with_ids.append({
            #         "id": point_id,
            #         "text": chunk,
            #         "metadata": {
            #             "filename": pdf_filename,
            #             "chunk_index": i
            #         }
            #     })
            
            # Store chunks with proper IDs
            print(f"store_chunks 123")
            logger.debug("store_chunks")
            # resume_rag_vector_store.store_chunks(chunks_with_ids, pdf_filename)
            resume_rag_vector_store.store_chunks(chunks, pdf_filename)
            
            add_embedded_pdf(pdf_filename)
            processed_count += 1
            logger.info(f"Finished processing and tracking PDF: {pdf_filename}")
        
        return {"message": f"Successfully processed {processed_count} new PDF(s)."}
    
    except Exception as e:
        logger.error(f"Error processing PDFs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process PDFs: {e}")
