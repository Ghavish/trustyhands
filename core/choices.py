"""Fixed lists of options shared by every app."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class District(models.TextChoices):
    PORT_LOUIS = "PORT_LOUIS", "Port Louis"
    PAMPLEMOUSSES = "PAMPLEMOUSSES", "Pamplemousses"
    RIVIERE_DU_REMPART = "RIVIERE_DU_REMPART", "Rivière du Rempart"
    FLACQ = "FLACQ", "Flacq"
    GRAND_PORT = "GRAND_PORT", "Grand Port"
    SAVANNE = "SAVANNE", "Savanne"
    PLAINES_WILHEMS = "PLAINES_WILHEMS", "Plaines Wilhems"
    MOKA = "MOKA", "Moka"
    BLACK_RIVER = "BLACK_RIVER", "Black River"
    ISLAND_WIDE = "ISLAND_WIDE", _("Island Wide")


class JobType(models.TextChoices):
    PLUMBING = "PLUMBING", _("Plumbing")
    REPAIRS = "REPAIRS", _("Repairs")
    MAINTENANCE = "MAINTENANCE", _("Maintenance")
    INSPECTION = "INSPECTION", _("Inspection")
    INSTALLATION = "INSTALLATION", _("Installation")
    OTHER = "OTHER", _("Other")


class Availability(models.TextChoices):
    AVAILABLE = "AVAILABLE", _("Available")
    BUSY = "BUSY", _("Busy")
    ON_LEAVE = "ON_LEAVE", _("On Leave")


class ProjectScale(models.TextChoices):
    SMALL = "SMALL", _("Small")
    MEDIUM = "MEDIUM", _("Medium")
    LARGE = "LARGE", _("Large")


class ClientType(models.TextChoices):
    RESIDENTIAL = "RESIDENTIAL", _("Residential")
    COMMERCIAL = "COMMERCIAL", _("Commercial")
    BOTH = "BOTH", _("Residential & Commercial")
