from fastapi import FastAPI
from app import init_db

app = FastAPI() # instance of FastAPI

app.title = "CatS"
app.version = "1.0.0"
