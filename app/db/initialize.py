from app.db.session import engine
from app.db.models import Base

def initialize_database():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    initialize_database()