from app.database import Base, engine, get_db
from sqlalchemy_utils import create_database, database_exists
from app import models


if not database_exists(engine.url):
    print("database_exist?")
    create_database(engine.url)
Base.metadata.create_all(bind=engine)
"""
from models import Community
get_db.add(
    Community(id=0, name="Test_0", description="Test_0_description")
)
get_db.commit()
print("Initialized the db")
"""