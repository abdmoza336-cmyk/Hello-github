import time

from anyio import current_time 
from session_service import RedisManager
from auth import authenticate_user

class RateLimiter:
    def __init__(self, max_requests, time_window):
        self.max_requests = max_requests
        self.time_window = time_window
        self.redis = RedisManager().redis
    def check_rate_limit(self, user_id: str) -> bool:
        if not user_id:
            return False  # No user ID provided, cannot check rate limit
           
        current_time = int(time.time())        # Get the current time in seconds for the rate limit check
        rate_key = f"rate_limit:{user_id}"          # Create a unique key for the user in Redis
        pipe= self.redis.pipeline()                     # Create a Redis pipeline for atomic operations
        pipe.zremrangebyscore(rate_key, 0, current_time - self.time_window)  # Remove requests that are outside the time window
        pipe.zcard(rate_key)                  # Get the current number of requests in the time window       
        current_requests = pipe.execute()[1]  # Execute the pipeline and get the current request count
        if current_requests >= self.max_requests:  # Check if the current request count exceeds the maximum allowed requests
            return False  # Rate limit exceeded
        else:
            pipe.zadd(rate_key, {current_time: current_time})  # Add the current request timestamp to the sorted set
            pipe.expire(rate_key, self.time_window)  # Set an expiration time for the key to automatically clean up old requests
            pipe.execute()  # Execute the pipeline to update Redis
            return True  # Request is allowed
        

RateLimiter=RateLimiter(max_requests=3, time_window=3600)  # Create an instance of the RateLimiter class with a maximum of 3 requests per hour
        