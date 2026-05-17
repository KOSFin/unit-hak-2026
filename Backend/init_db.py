from app.core.database import engine, Base
import app.models

Base.metadata.create_all(bind=engine)
print("DB created directly from models.")
