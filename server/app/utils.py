import logging
import time
from functools import wraps

def rate_limit(max_calls: int, time_window: int):
    """Simple rate limiting decorator"""
    calls = []
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_time = time.time()
            calls_in_window = [call for call in calls if call > current_time - time_window]
            
            if len(calls_in_window) >= max_calls:
                raise Exception("Rate limit exceeded")
            
            calls.append(current_time)
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def setup_logging():
    """Setup application logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('app.log')
        ]
    )