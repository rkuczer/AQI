from cryptography.fernet import Fernet
import string
import os
import secrets

# Generate a key for encryption
key = Fernet.generate_key()
cipher_suite = Fernet(key)


def generate_password(length=15):
    """Generate a random password with a given length."""
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(characters) for _ in range(length))
    return password


def encrypt_password(password):
    """Encrypt a password using the Fernet symmetric encryption algorithm."""
    encrypted_password = cipher_suite.encrypt(password.encode())
    return encrypted_password


def decrypt_password(encrypted_password):
    """Decrypt an encrypted password."""
    decrypted_password = cipher_suite.decrypt(encrypted_password).decode()
    return decrypted_password


def save_password_to_file(password, filename):
    """Encrypt and save a password to a file."""
    encrypted_password = encrypt_password(password)
    with open(filename, 'wb') as file:
        file.write(encrypted_password)


def get_password_from_file(filename):
    """Retrieve and decrypt a password from a file."""
    with open(filename, 'rb') as file:
        encrypted_password = file.read()
    decrypted_password = decrypt_password(encrypted_password)
    return decrypted_password


def main():
    # Example of generating a password
    new_password = generate_password()
    print(f"Generated Password: {new_password}")

    # Save the generated password to an encrypted file
    save_password_to_file(new_password, "encrypted_password.txt")

    # Example of retrieving and decrypting a password from the file
    retrieved_password = get_password_from_file("encrypted_password.txt")
    print(f"Retrieved Password: {retrieved_password}")


if __name__ == "__main__":
    main()
