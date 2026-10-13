import os
from dotenv import load_dotenv
import redis

# Load environment variables (or paste your URL directly for testing)
load_dotenv()
redis_url = os.getenv("REDIS_URL")

print(f"Testing connection to: {redis_url}")

try:
    # Connect directly using the URL
    r = redis.Redis.from_url(redis_url, decode_responses=True)

    # Test ping
    response = r.ping()
    print(f"✅ Ping Result: {response}")

    # Test write and read
    r.set("connection_test", "Success!")
    val = r.get("connection_test")
    print(f"✅ Read/Write Test Result: {val}")

except Exception as e:
    print(f"❌ Connection Failed: {e}")