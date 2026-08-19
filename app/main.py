# docker start ollama
from fastapi import FastAPI
from pydantic import BaseModel

from llm.ollama import generate


app = FastAPI()


class Question(BaseModel):
    question: str


@app.get("/")
def root():
    return {"message": "Research Agent funcionando"}


@app.post("/ask")
def ask(data: Question):

    answer = generate(data.question)

    return {
        "response": answer
    }