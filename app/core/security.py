from pwdlib import PasswordHash

# Modern, secure password hashing using Argon2
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Hashes a plaintext password securely."""
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against the stored hash."""
    return password_hash.verify(plain_password, hashed_password)