import bcrypt


def generate_salt() -> str:
    return bcrypt.gensalt(14)


def create_bcrypt_hash(password: str, salt: str) -> str:
    password_bytes = password.encode()
    password_hash_bytes = bcrypt.hashpw(password_bytes, salt)
    return password_hash_bytes.decode()


def verify_password(password: str, hash_from_database: str) -> bool:
    password_bytes = password.encode()
    hash_bytes = hash_from_database.encode()

    return bcrypt.checkpw(password_bytes, hash_bytes)
