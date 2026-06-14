from db import Base, engine
from models import Feedback
from models import User
from models import Product
from models import Category
from models import Tag
from models import ProductFeedback

Base.metadata.create_all(bind=engine)

print("Tables created successfully!")
