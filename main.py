from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import Column, Integer, String, Text, create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, EmailStr, constr
from typing import List
import secrets
import time
from passlib.context import CryptContext
from cachetools import TTLCache
from dotenv import load_dotenv
import os

# Load environment variables from .env file for database configuration
load_dotenv()

# In-memory cache with TTL (Time-To-Live) of 300 seconds (5 minutes) for posts
cache = TTLCache(maxsize=100, ttl=300) 

# Database connection string from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

# Setting up SQLAlchemy engine, session maker, and base class
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing context (bcrypt) for securely hashing passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Utility functions for password hashing and verification
def hash_password(password: str) -> str:
    """
    Hash the password using bcrypt.
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify the plain password against the hashed password.
    """
    return pwd_context.verify(plain_password, hashed_password)

# Database Models (SQLAlchemy)
class User(Base):
    """
    User model representing the 'users' table in the database.
    """
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)  # Email should be unique
    password = Column(String(255))  # Password field
    token = Column(String(255), unique=True, index=True, nullable=True)  # Token for authentication


class Post(Base):
    """
    Post model representing the 'posts' table in the database.
    """
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text)  # Text content of the post
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))  # Foreign key linking to User
    created_at = Column(Integer, default=int(time.time()))  # Timestamp when post was created

# Create tables in the database
Base.metadata.create_all(bind=engine)

# Pydantic Schemas for request validation
class UserCreate(BaseModel):
    """
    Pydantic model to validate user data for account creation (signup).
    """
    email: EmailStr  # Validate that the email is a valid email string
    password: constr(min_length=6)  # Password should be at least 6 characters long

class UserLogin(BaseModel):
    """
    Pydantic model to validate user data for login.
    """
    email: EmailStr  # Validate that the email is a valid email string
    password: str  # Plaintext password for login

class PostCreate(BaseModel):
    """
    Pydantic model to validate the data when creating a post.
    """
    text: constr(max_length=1048576)  # Text length limit of 1 MB (1,048,576 bytes)

class PostResponse(BaseModel):
    """
    Pydantic model for the response format when retrieving posts.
    """
    id: int
    text: str
    user_id: int
    created_at: int

# Dependency to handle the database session lifecycle
def get_db():
    """
    Dependency function to provide the database session.
    Ensures session is properly handled (commit/rollback) and closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        db.rollback()  # Rollback the session if there's an exception
        raise e
    finally:
        db.close()  # Always close the session

# FastAPI App Initialization
app = FastAPI()

# Authentication Helper function
def get_user_by_token(db: Session, token: str):
    """
    Retrieve a user from the database based on the provided token.
    """
    return db.query(User).filter(User.token == token).first()

# API Endpoints

@app.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    """
    Endpoint for user signup.
    - Validates user data (email and password).
    - Checks if the email is already registered.
    - Hashes the password and generates a token for the user.
    - Returns the generated token.
    """
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pw = hash_password(user.password)
    new_user = User(email=user.email, password=hashed_pw, token=secrets.token_hex(16))
    db.add(new_user)
    db.commit()
    return {"token": new_user.token}

@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    """
    Endpoint for user login.
    - Validates user credentials (email and password).
    - Returns a token upon successful login.
    - Returns error for invalid credentials.
    """
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"token": db_user.token}

@app.post("/addpost")
def add_post(post: PostCreate, token: str, db: Session = Depends(get_db)):
    """
    Endpoint to add a new post.
    - Validates token for authentication.
    - Saves the post to the database.
    - Returns the post ID.
    """
    user = get_user_by_token(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    new_post = Post(text=post.text, user_id=user.id)
    db.add(new_post)
    db.commit()
    return {"postID": new_post.id}

@app.get("/getposts", response_model=List[PostResponse])
def get_posts(token: str, db: Session = Depends(get_db)):
    """
    Endpoint to get all posts by a user.
    - Validates token for authentication.
    - Returns cached posts if available, otherwise queries the database.
    - Caches the posts for 5 minutes to improve performance.
    """
    user = get_user_by_token(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    
    # Check if the posts are already cached for the user
    if token in cache:
        return cache[token]

    posts = db.query(Post).filter(Post.user_id == user.id).all()

    # Cache the posts for 5 minutes
    cache[token] = posts
    return posts

@app.delete("/deletepost/{post_id}")
def delete_post(post_id: int, token: str, db: Session = Depends(get_db)):
    """
    Endpoint to delete a post by ID.
    - Validates token for authentication.
    - Deletes the post if it exists and belongs to the user.
    """
    user = get_user_by_token(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    post = db.query(Post).filter(Post.id == post_id, Post.user_id == user.id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    db.delete(post)
    db.commit()
    return {"detail": "Post deleted"}
