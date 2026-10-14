import hashlib
import secrets
from session_service import RedisManager

# Get the Redis client
r = RedisManager().redis

def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """Securely hash a password using PBKDF2-HMAC with a unique salt."""
    if not salt:
        salt = secrets.token_hex(16)
    # Hash the password with 100,000 iterations of SHA-256
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256', 
        password.encode('utf-8'), 
        salt.encode('utf-8'), 
        100000
    ).hex()
    return pwd_hash, salt

def register_user(email: str, password: str, name: str) -> tuple[bool, str]:
    """Register a new user and store them in Redis. Returns (success, message_or_user_id)."""
    email = email.strip().lower()
    user_key = f"user:email:{email}"
    
    # Check if email already exists in Redis
    if r.exists(user_key):
        return False, "An account with this email already exists."
    
    # Generate a unique user ID and hash the password
    user_id = secrets.token_urlsafe(16)
    pwd_hash, salt = hash_password(password)
    
    # User profile data dictionary
    user_data = {
        "user_id": user_id,
        "name": name,
        "email": email,
        "password_hash": pwd_hash,
        "salt": salt
    }
    
    # Save user info in Redis (using a hash for profile and a lookup key for email)
    pipe = r.pipeline()
    pipe.hset(f"user:profile:{user_id}", mapping=user_data)
    pipe.set(user_key, user_id)
    pipe.execute()
    
    return True, user_id

def authenticate_user(email: str, password: str) -> dict | None:
    """Verify user credentials against Redis. Returns user profile dict if valid, else None."""
    email = email.strip().lower()
    user_key = f"user:email:{email}"
    
    # Get user_id from email lookup
    user_id = r.get(user_key)
    if not user_id:
        return None
        
    # Fetch user profile from Redis
    user_profile = r.hgetall(f"user:profile:{user_id}")
    if not user_profile:
        return None
        
    # Verify password hash
    stored_hash = user_profile.get("password_hash")
    salt = user_profile.get("salt")
    
    test_hash, _ = hash_password(password, salt)
    
    if test_hash == stored_hash:
        return {
            "user_id": user_profile.get("user_id"),
            "name": user_profile.get("name"),
            "email": user_profile.get("email")
        }
        
    return None