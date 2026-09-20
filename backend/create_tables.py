from app.database import engine
from app.models import Base
import app.content_models  # ensures ContentResource is registered before create_all runs

Base.metadata.create_all(bind=engine)
print("All tables created successfully in Supabase.")