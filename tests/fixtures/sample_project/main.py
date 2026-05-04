"""Point d'entrée principal du mini-projet de test."""

from models import User, AdminUser, hash_password


def main():
    """Fonction principale."""
    user = User(name="Bouchra", email="bouchra@liad.ma", age=23)
    print(f"Utilisateur: {user.full_name()}")
    print(f"Adulte: {user.is_adult}")

    hashed = hash_password("secret123")
    print(f"Hash: {hashed}")


if __name__ == "__main__":
    main()
