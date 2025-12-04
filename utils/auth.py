"""
Authentication system with JSON file storage and JWT tokens
"""
import json
import os
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path

from jose import jwt, JWTError
from pydantic import BaseModel

from models.schemas import User, UserCreate, Token, TokenData


# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production-920654cb695ee99175e53d6da8dc2edf")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# JSON storage file
DATA_DIR = Path(__file__).parent.parent / "data"
USERS_FILE = DATA_DIR / "users.json"


def ensure_data_dir():
    """Ensure data directory exists"""
    DATA_DIR.mkdir(exist_ok=True)
    if not USERS_FILE.exists():
        USERS_FILE.write_text("[]")


def load_users() -> list:
    """Load users from JSON file"""
    ensure_data_dir()
    try:
        return json.loads(USERS_FILE.read_text())
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_users(users: list):
    """Save users to JSON file"""
    ensure_data_dir()
    USERS_FILE.write_text(json.dumps(users, indent=2))


def hash_password(password: str, salt: str = None) -> tuple:
    """Hash password with SHA256 + salt"""
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${hashed}", salt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        salt, stored_hash = hashed_password.split('$')
        _, new_hash_salt = hash_password(plain_password, salt)
        check_hash = hashlib.sha256((plain_password + salt).encode()).hexdigest()
        return check_hash == stored_hash
    except:
        return False


def get_password_hash(password: str) -> str:
    """Hash a password"""
    hashed, _ = hash_password(password)
    return hashed


def get_user_by_username(username: str) -> Optional[dict]:
    """Get user by username"""
    users = load_users()
    for user in users:
        if user["username"] == username:
            return user
    return None


def get_user_by_email(email: str) -> Optional[dict]:
    """Get user by email"""
    users = load_users()
    for user in users:
        if user["email"] == email:
            return user
    return None


def create_user(user_data: UserCreate) -> User:
    """Create a new user"""
    users = load_users()
    
    # Check if username or email exists
    if get_user_by_username(user_data.username):
        raise ValueError("Username already exists")
    if get_user_by_email(user_data.email):
        raise ValueError("Email already exists")
    
    # Create new user
    new_user = {
        "id": str(uuid.uuid4()),
        "username": user_data.username,
        "email": user_data.email,
        "hashed_password": get_password_hash(user_data.password),
        "created_at": datetime.utcnow().isoformat()
    }
    
    users.append(new_user)
    save_users(users)
    
    return User(
        id=new_user["id"],
        username=new_user["username"],
        email=new_user["email"],
        created_at=new_user["created_at"]
    )


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate a user"""
    user = get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[TokenData]:
    """Verify a JWT token and return token data"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return TokenData(username=username)
    except JWTError:
        return None


def get_current_user(token: str) -> Optional[User]:
    """Get the current user from a token"""
    token_data = verify_token(token)
    if not token_data or not token_data.username:
        return None
    
    user_data = get_user_by_username(token_data.username)
    if not user_data:
        return None
    
    return User(
        id=user_data["id"],
        username=user_data["username"],
        email=user_data["email"],
        created_at=user_data["created_at"]
    )
