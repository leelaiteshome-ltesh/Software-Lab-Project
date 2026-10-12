"""Custom cipher from the Python Programming HW.

Steps: reverse the text, then shift every character N positions
(D = +1 right, D = -1 left), wrapping inside ASCII 34..126 so the
result never contains a space (32) or "!" (33).
"""

MIN_CHAR = 34
MAX_CHAR = 126
CHAR_RANGE = MAX_CHAR - MIN_CHAR + 1  # 93 usable characters


def _validate(text, N, D):
    if not isinstance(text, str):
        raise ValueError("Text must be a string")
    if not isinstance(N, int) or N < 1:
        raise ValueError("N must be an integer >= 1")
    if D not in (1, -1):
        raise ValueError("D must be 1 (shift right) or -1 (shift left)")
    for ch in text:
        if not MIN_CHAR <= ord(ch) <= MAX_CHAR:
            raise ValueError("Text can't contain spaces, '!' or non-printable characters")


def _shift(text, amount):
    return "".join(
        chr((ord(ch) - MIN_CHAR + amount) % CHAR_RANGE + MIN_CHAR) for ch in text
    )


def encrypt(inputText, N, D):
    _validate(inputText, N, D)
    return _shift(inputText[::-1], N * D)


def decrypt(encryptedText, N, D):
    _validate(encryptedText, N, D)
    return _shift(encryptedText, -N * D)[::-1]
