import pytest
import string
from project import generate_passwd, check_passwd_strength, hash_password



def test_generate_passwd():
    pwd = generate_passwd(12)
    assert len(pwd) == 12
    valid_chars = string.ascii_letters + string.digits + string.punctuation
    for ch in pwd:
        assert ch in valid_chars


def test_check_passwd_strength():
    assert check_passwd_strength("Abc123!@") > 80
    with pytest.raises(ValueError):
        check_passwd_strength("abc")


def test_hash_password():
    salt = b'saltysalt'
    h1 = hash_password("mypass", salt)
    h2 = hash_password("mypass", salt)
    assert h1 == h2
    h3 = hash_password("mypass2", salt)
    assert h1 != h3
