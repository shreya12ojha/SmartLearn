from app.database import engine
from app.models import Base
from app.content_models import ContentResource  # registers the new table with Base

Base.metadata.create_all(bind=engine)

print("Existing tables kept. New missing tables created successfully.")