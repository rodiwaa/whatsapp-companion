# scripts/setup_resume_data.py
from utils.resume_rag import ResumeRAG
import PyPDF2  # or your preferred PDF reader

FILE_PATH = ".personal/resume.pdf"

def extract_resume_chunks(pdf_path):
    # Extract text from your resume PDF
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    
    # Split into meaningful chunks (by section, paragraph, etc.)
    chunks = text.split('\n\n')  # Simple splitting, adjust as needed
    return [chunk.strip() for chunk in chunks if chunk.strip()]

def main():
    resume_rag = ResumeRAG()
    resume_rag.setup_collection()
    
    # Process your resume
    chunks = extract_resume_chunks(FILE_PATH)
    resume_rag.add_resume_chunks(chunks)
    
    print(f"Added {len(chunks)} resume chunks to Qdrant collection")

if __name__ == "__main__":
    main()
