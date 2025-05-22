from app.database import Base, engine, SessionLocal
from app import models
from app.models import Community
from sqlalchemy_utils import create_database, database_exists

if not database_exists(engine.url):
    print("database does not exist, creating...")
    create_database(engine.url)

Base.metadata.create_all(bind=engine)
print('Tables created successfully')