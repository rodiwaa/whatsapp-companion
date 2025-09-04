from fastapi import FastAPI
from ai_companion.interfaces.resume_ragger.app import resume_ragger_router

app = FastAPI(
    title="Resume Ragger Document Processing API",
    description="API for uploading and processing PDF documents for the Resume Ragger.",
    version="1.0.0",
)

app.include_router(resume_ragger_router)
