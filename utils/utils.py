import string
import random
import time

import hashlib

def stringToMd5(text):
    return hashlib.md5(text.encode()).hexdigest()

def getRandomString(min, max):

    # Create a list of all possible characters.
    # Uppercase, lowercase, and digits.
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits

    # Generate random string length between min and max
    length = random.randint(min, max)
    
    # Generate and return a random string
    return ''.join(random.choice(chars) for _ in range(length))

def getTimeMillis():
	return int(round(time.time() * 1000))