from fastapi import FastAPI
from database import engine, Base

app = FastAPI() # instance of FastAPI
Base.metadata.create_all(bind=engine)

app.title = "CatS"
app.version = "1.0.0"