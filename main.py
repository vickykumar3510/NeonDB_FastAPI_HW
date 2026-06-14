from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from db import SessionLocal, engine, Base
from models import User, Product, Feedback, Category, Tag, ProductFeedback
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(title="NeonDB + FastAPI Demo")

# --- Database setup ---
# Create all tables at startup
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- User models ---
## pydantic model for user request body
class UserCreate(BaseModel):
    name: str
    email: str

## pydantic model for user response
class UserResponse(BaseModel):
    id: int
    name: str
    email: str

    # Pydantic v2 fix
    model_config = ConfigDict(from_attributes=True)

# --- Product models ---
## pydantic model for product request body
class ProductCreate(BaseModel):
    product_id: int
    product_name: str
    quantity: int = Field(ge=0) 
    in_stock: bool = True

## pydantic model for product response
class ProductResponse(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    in_stock: bool
    is_archived: bool

    model_config = ConfigDict(from_attributes=True)

# --- Feedback models ---

class FeedbackCreate(BaseModel):
    name: str
    comment: str

class FeedbackResponse(BaseModel):
    id: int
    name: str
    comment: str

    model_config = ConfigDict(from_attributes=True)

# -- Category models ---

class CategoryCreate(BaseModel):
    name: str

class CategoryResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)

# -- Tag models ---

class TagCreate(BaseModel):
    name: str

class TagResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)

# -- Product feedback --

class ProductFeedbackCreate(BaseModel):
    product_id: int
    comment: str
    rating: int = Field(ge=1, le=5) 


class ProductFeedbackResponse(BaseModel):
    id: int
    product_id: int
    comment: str
    rating: int

    model_config = ConfigDict(from_attributes=True)


# --- Routes ---

# user POST route
@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered.")
    
    new_user = User(name=user.name, email=user.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# user GET route
@app.get("/users/", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

# feeback POST route
@app.post("/feedback", response_model=FeedbackResponse)
def create_feedback(feedback: FeedbackCreate, db: Session = Depends(get_db)):
    existing_feedback = db.query(Feedback).filter(Feedback.name == feedback.name).first()
    if existing_feedback:
        raise HTTPException(
            status_code=400,
            detail=f"Feedback from {feedback.name} already exists"
        )

    new_feedback = Feedback(name=feedback.name, comment=feedback.comment)
    db.add(new_feedback)
    db.commit()
    db.refresh(new_feedback)
    return new_feedback

# GET feedback by NAME
@app.get("/feedback", response_model=list[FeedbackResponse])
def get_feedback(name: str | None = None, db: Session = Depends(get_db)):
    if name:
        feedbacks = db.query(Feedback).filter(Feedback.name == name).all()
    else:
        feedbacks = db.query(Feedback).all()
    return feedbacks


# category POST route
@app.post("/categories", response_model=CategoryResponse)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    existing_category = db.query(Category).filter(Category.name == category.name).first()
    if existing_category:
        raise HTTPException(
            status_code=400,
            detail=f"Category '{category.name}' already exists"
        )

    new_category = Category(name=category.name)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

# category GET route
@app.get("/categories", response_model=list[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).all()
    return categories

# tag POST route
@app.post("/tags", response_model=TagResponse)
def create_tag(tag: TagCreate, db: Session = Depends(get_db)):
    new_tag = Tag(name=tag.name)
    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)
    return new_tag

# product POST route
@app.post("/products", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    new_product = Product(
        product_id=product.product_id,
        product_name=product.product_name,
        quantity=product.quantity,
        in_stock=product.in_stock
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

# product GET route
@app.get("/products", response_model=list[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return products

# product Soft-Delete Simulation — “Archive” a Product --- IT IS NOT WORKING
@app.post("/products/{product_id}/archive", response_model=ProductResponse)
def archive_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.is_archived = True
    db.commit()
    db.refresh(product)
    return product

# GET product by NAME
@app.get("/products/search", response_model=list[ProductResponse])
def search_products(name: str, db: Session = Depends(get_db)):
    results = db.query(Product).filter(Product.product_name.ilike(f"%{name}%")).all()
    return results

# POST product feedback
@app.post("/product-feedback", response_model=ProductFeedbackResponse)
def create_product_feedback(feedback: ProductFeedbackCreate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.product_id == feedback.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.is_archived:
        raise HTTPException(status_code=400, detail="Cannot review archived product")

    new_feedback = ProductFeedback(
        product_id=feedback.product_id,
        comment=feedback.comment,
        rating=feedback.rating
    )
    db.add(new_feedback)
    db.commit()
    db.refresh(new_feedback)
    return new_feedback



# Optional root health check
@app.get("/")
def root():
    return {"message": "API is running"}
