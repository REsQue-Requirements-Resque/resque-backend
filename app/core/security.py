import bcrypt


def get_password_hash(password: str) -> str:
    # 비밀번호를 바이트로 인코딩
    password_bytes = password.encode("utf-8")
    # salt 생성 및 해싱
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    # 바이트를 문자열로 디코딩하여 반환
    return hashed_bytes.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # 비밀번호와 해시를 바이트로 인코딩
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    # bcrypt의 checkpw 함수를 사용하여 검증
    return bcrypt.checkpw(password_bytes, hashed_bytes)
