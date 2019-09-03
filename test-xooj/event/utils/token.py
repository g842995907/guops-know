import hashlib
import uuid

def generate_signup_token():
	return hashlib.md5(str(uuid.uuid4())).hexdigest()

def generate_random_password():
	return generate_signup_token()[:10]