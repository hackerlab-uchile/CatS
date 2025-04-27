from app.database import Base, engine
from sqlalchemy_utils import create_database, database_exists
from app import models

def init_db():
    if not database_exists(engine.url):
        create_database(engine.url)
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()