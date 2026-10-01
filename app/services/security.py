import base64
import hashlib
import os
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


ph = PasswordHasher()


def hash_master_password(password: str) -> str:
    return ph.hash(password)


def verify_master_password(password: str, password_hash: str) -> bool:
    try:
        return ph.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError):
        return False


def make_salt() -> bytes:
    return secrets.token_bytes(16)


def derive_key(master_password: str, salt: bytes) -> bytes:
    """
    Derive a 256-bit encryption key from the master password.

    n=2**14 keeps memory usage reasonable for environments
    where OpenSSL imposes a relatively small memory limit.
    """

    return hashlib.scrypt(
        master_password.encode("utf-8"),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
        dklen=32,
        maxmem=64 * 1024 * 1024,
    )


def encrypt_text(plaintext: str, key: bytes) -> str:
    nonce = os.urandom(12)

    ciphertext = AESGCM(key).encrypt(
        nonce,
        plaintext.encode("utf-8"),
        None,
    )

    return base64.urlsafe_b64encode(
        nonce + ciphertext
    ).decode("ascii")


def decrypt_text(token: str, key: bytes) -> str:
    raw = base64.urlsafe_b64decode(
        token.encode("ascii")
    )

    nonce = raw[:12]
    ciphertext = raw[12:]

    return AESGCM(key).decrypt(
        nonce,
        ciphertext,
        None,
    ).decode("utf-8")


def generate_password(length: int = 24) -> str:
    alphabet = (
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789"
        "!@#$%^&*()-_=+"
    )

    return "".join(
        secrets.choice(alphabet)
        for _ in range(length)
    )