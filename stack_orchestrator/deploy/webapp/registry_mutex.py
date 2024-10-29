from functools import wraps
import os
import time

# Define default file path for the lock
DEFAULT_LOCK_FILE_PATH = "/tmp/registry_mutex_lock_file"
LOCK_TIMEOUT = 30
LOCK_RETRY_INTERVAL = 3


def acquire_lock(client, lock_file_path, timeout):
    # Lock alreay acquired by the current client
    if client.mutex_lock_acquired:
        return

    while True:
        try:
            # Check if lock file exists and is potentially stale
            if os.path.exists(lock_file_path):
                with open(lock_file_path, 'r') as lock_file:
                    timestamp = float(lock_file.read().strip())

                # If lock is stale, remove the lock file
                if time.time() - timestamp > timeout:
                    print(f"Stale lock detected, removing lock file {lock_file_path}")
                    os.remove(lock_file_path)
                else:
                    print(f"Lock file {lock_file_path} exists and is recent, waiting...")
                    time.sleep(LOCK_RETRY_INTERVAL)
                    continue

            # Try to create a new lock file with the current timestamp
            fd = os.open(lock_file_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            with os.fdopen(fd, 'w') as lock_file:
                lock_file.write(str(time.time()))

            client.mutex_lock_acquired = True
            print(f"Registry lock acquired, {lock_file_path}")

            # Lock successfully acquired
            return

        except FileExistsError:
            print(f"Lock file {lock_file_path} exists, waiting...")
            time.sleep(LOCK_RETRY_INTERVAL)


def release_lock(client, lock_file_path):
    try:
        os.remove(lock_file_path)

        client.mutex_lock_acquired = False
        print(f"Registry lock released, {lock_file_path}")
    except FileNotFoundError:
        # Lock file already removed
        pass


def registry_mutex():
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            lock_file_path = DEFAULT_LOCK_FILE_PATH
            if self.mutex_lock_file:
                lock_file_path = self.mutex_lock_file

            # Acquire the lock before running the function
            acquire_lock(self, lock_file_path, LOCK_TIMEOUT)
            try:
                return func(self, *args, **kwargs)
            finally:
                # Release the lock after the function completes
                release_lock(self, lock_file_path)

        return wrapper

    return decorator
