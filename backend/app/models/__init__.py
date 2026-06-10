"""Exporte tous les modèles pour l'enregistrement SQLAlchemy et les imports."""
from .company import Company
from .user import User
from .training import Training
from .room import Room
from .booking import Booking

__all__ = ["Company", "User", "Training", "Room", "Booking"]
