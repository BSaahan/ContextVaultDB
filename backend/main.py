from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from backend.database import engine, Base, get_db
from backend import models, schemas

from backend.embeddings import generate_embedding

from backend.retrieval import cosine_similarity

from fastapi import UploadFile, File
from backend.ingestion import extract_text_from_pdf, chunk_text

from backend.chat import generate_chat_response

app = FastAPI(
    title="ContextVaultDB",
    description="A mini AI memory database inspired by HydraDB",
    version="0.1.0"
)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def home():
    return {"message": "ContextVaultDB is running", "status": "success"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/memory/add", response_model=schemas.MemoryResponse)
def add_memory(memory: schemas.MemoryCreate, db: Session = Depends(get_db)):
    embedding = generate_embedding(memory.content)

    new_memory = models.Memory(
        title=memory.title,
        content=memory.content,
        category=memory.category,
        embedding=embedding
    )

    db.add(new_memory)
    db.commit()
    db.refresh(new_memory)

    return new_memory

@app.get("/memory/all")
def get_all_memories(db: Session = Depends(get_db)):
    memories = db.query(models.Memory).all()
    return memories

@app.post("/memory/search")
def search_memory(search: schemas.MemorySearch, db: Session = Depends(get_db)):
    query_embedding = generate_embedding(search.query)

    memories = db.query(models.Memory).all()

    results = []

    for memory in memories:
        if memory.embedding is not None:
            score = cosine_similarity(query_embedding, memory.embedding)

            results.append({
                "id": memory.id,
                "title": memory.title,
                "content": memory.content,
                "category": memory.category,
                "similarity_score": float(score)
            })

    results = sorted(
        results,
        key=lambda x: x["similarity_score"],
        reverse=True
    )

    return results[:search.top_k]

@app.post("/document/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    file_path = f"temp_{file.filename}"

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    extracted_text = extract_text_from_pdf(file_path)
    chunks = chunk_text(extracted_text)

    saved_chunks = []

    for i, chunk in enumerate(chunks):
        embedding = generate_embedding(chunk)

        new_memory = models.Memory(
            title=f"{file.filename} - chunk {i + 1}",
            content=chunk,
            category="document",
            embedding=embedding
        )

        db.add(new_memory)
        db.commit()
        db.refresh(new_memory)

        saved_chunks.append(new_memory.id)

    return {
        "message": "Document uploaded and chunked successfully",
        "filename": file.filename,
        "total_chunks": len(saved_chunks),
        "chunk_ids": saved_chunks
    }

from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_chat_response(context, question):

    prompt = f"""
    Use the following context to answer the question.

    Context:
    {context}

    Question:
    {question}
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content

@app.post("/chat")
def chat_with_memory(request: schemas.ChatRequest, db: Session = Depends(get_db)):
    query_embedding = generate_embedding(request.question)

    memories = db.query(models.Memory).all()
    results = []

    for memory in memories:
        if memory.embedding is not None:
            score = cosine_similarity(query_embedding, memory.embedding)

            results.append({
                "content": memory.content,
                "score": float(score)
            })

    results = sorted(results, key=lambda x: x["score"], reverse=True)
    top_results = results[:request.top_k]

    context = "\n\n".join([item["content"] for item in top_results])

    answer = generate_chat_response(context, request.question)

    return {
        "question": request.question,
        "answer": answer,
        "sources_used": top_results
    }