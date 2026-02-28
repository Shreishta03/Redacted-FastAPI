import hashlib
import os

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    pwd_hash = hashlib.sha256(salt + password.encode()).hexdigest()
    return salt.hex() + ":" + pwd_hash

def verify_password(plain_password: str, stored_password: str) -> bool:
    salt_hex, pwd_hash = stored_password.split(":")
    salt = bytes.fromhex(salt_hex)
    check_hash = hashlib.sha256(salt + plain_password.encode()).hexdigest()
    return check_hash == pwd_hash
