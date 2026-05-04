"""
Fichier fixture pour tester le parser Python.
Contient volontairement différents types d'entités Python.

Ce fichier NE SERA PAS exécuté, il sera seulement PARSÉ par le module d'analyse.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Optional, List

# Variable globale simple
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30.0
_PRIVATE_CONSTANT = "secret_value"

logger = logging.getLogger(__name__)


@dataclass
class User:
    """Représente un utilisateur du système."""
    name: str
    email: str
    age: int = 0
    roles: List[str] = field(default_factory=list)

    def full_name(self) -> str:
        """Retourne le nom complet."""
        return self.name

    @property
    def is_adult(self) -> bool:
        return self.age >= 18

    @staticmethod
    def validate_email(email: str) -> bool:
        """Vérifie que l'email est valide."""
        return "@" in email


class AdminUser(User):
    """Un utilisateur avec des droits d'administration."""

    def __init__(self, name: str, email: str, permissions: List[str] = None):
        super().__init__(name=name, email=email)
        self.permissions = permissions or []

    async def revoke_access(self, target_user: User) -> bool:
        """Révoque l'accès d'un utilisateur."""
        logger.info(f"Revoking access for {target_user.name}")
        return True


def hash_password(raw_password: str, salt: str = "default") -> str:
    """Hash un mot de passe avec un sel."""
    import hashlib
    return hashlib.sha256(f"{salt}{raw_password}".encode()).hexdigest()


async def fetch_user_from_db(user_id: int, db=None) -> Optional[User]:
    """Récupère un utilisateur depuis la base de données."""
    if db is None:
        return None
    return User(name="Test", email="test@test.com")


def process_batch(
    items: List[str],
    *args,
    verbose: bool = False,
    **kwargs,
) -> int:
    """Traite un batch d'éléments."""
    count = 0
    for item in items:
        if verbose:
            print(f"Processing: {item}")
        count += 1
    return count
