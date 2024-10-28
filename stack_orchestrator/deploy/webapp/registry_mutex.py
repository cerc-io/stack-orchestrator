import fcntl
from functools import wraps

# Define default file path for the lock
DEFAULT_LOCK_FILE_PATH = "/tmp/registry_mutex_lock_file"


def registry_mutex():
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            lock_file_path = DEFAULT_LOCK_FILE_PATH
            if self.mutex_lock_file:
                lock_file_path = self.mutex_lock_file

            with open(lock_file_path, 'w') as lock_file:
                try:
                    # Try to acquire the lock
                    fcntl.flock(lock_file, fcntl.LOCK_EX)

                    # Call the actual function
                    result = func(self, *args, **kwargs)
                finally:
                    # Always release the lock
                    fcntl.flock(lock_file, fcntl.LOCK_UN)

            return result

        return wrapper

    return decorator
