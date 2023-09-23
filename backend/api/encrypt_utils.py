from passlib.context import CryptContext

crypto_context = CryptContext(schemes=["bcrypt"])


def verify_password(password: str, hashed_password: str) -> bool:
    """

    :param password: A real password entered by user
    :param hashed_password: Hashed password returned from database
    :return: bool
    """
    return crypto_context.verify(password, hashed_password)
