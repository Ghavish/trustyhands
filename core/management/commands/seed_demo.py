"""
Fills MongoDB with the sample data shown in the Figma screens.

Run:  python manage.py seed_demo
Run again from scratch:  python manage.py seed_demo --reset
Teammates sharing the same Atlas database only need the pictures:
      python manage.py seed_demo --media-only

Every demo account uses the password printed at the end.
"""

import datetime
import random
import re
import shutil
from decimal import Decimal
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import models
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from core import models as m
from core.choices import JobType

User = get_user_model()
IMAGES = Path(__file__).resolve().parent.parent / "seed_images"
PASSWORD = "TrustyHands@2026"
DOMAIN = "trustyhands.mu"

# Folders inside media/ that the demo data writes to.
MEDIA_FOLDERS = [
    "categories", "providers", "services", "portfolio", "profiles",
    "documents", "requests",
]
# Django adds "_AbC1234" to a file name when the name is already taken.
DJANGO_SUFFIX = re.compile(r"_[A-Za-z0-9]{7}(?=\.\w+$)")

# Sample licences, certificates, insurance notes and business registrations
# for the demo providers. They are clearly marked "SAMPLE - NOT A REAL
# DOCUMENT" and name a fictional issuer. Files are in seed_images/documents/.
DOCUMENTS = IMAGES / "documents"

# Review comments by star rating, so reviews read like real people wrote them.
REVIEW_COMMENTS = {
    5: [
        "Arrived on time, explained everything and left the place spotless.",
        "Fixed in one visit. Fair price and very polite.",
        "Excellent work, I will book again for the kitchen.",
        "Very professional. Sent photos of the work before leaving.",
        "Quick quote on WhatsApp and the job was done the next day.",
        "Careful and tidy. Took time to show me what was wrong.",
    ],
    4: [
        "Good job overall, came about 30 minutes late.",
        "Solid work. Price was a little higher than the first quote.",
        "Did what was needed. Had to come back once for a small fix.",
        "Friendly and knew the job well. Communication could be faster.",
    ],
    3: [
        "The work is fine but it took two visits to finish.",
        "OK result. Left some dust behind and had to reschedule once.",
    ],
    2: [
        "The repair held but the visit was rescheduled twice.",
    ],
}


def stars():
    """A realistic rating: mostly 4-5 stars, sometimes 3, rarely 2."""
    return random.choices([5, 4, 3, 2], weights=[64, 26, 8, 2])[0]


def comment_for(rating):
    return random.choice(REVIEW_COMMENTS[rating])


def document(filename):
    """Read one sample PDF from seed_images/documents/."""
    return ContentFile((DOCUMENTS / filename).read_bytes(), name=filename)


def backdate(instance, **fields):
    """Set auto_now_add dates (created_at, uploaded_at...) to a past time."""
    type(instance).objects.filter(pk=instance.pk).update(**fields)


# A tiny valid PDF used as a stand-in for uploaded documents.
SAMPLE_PDF = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 200]>>endobj\n"
    b"trailer<</Root 1 0 R>>\n%%EOF\n"
)


def image(folder, name):
    """Read one picture from core/management/seed_images/."""
    data = (IMAGES / folder / name).read_bytes()
    return ContentFile(data, name=name)


def slug(text):
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def days_ago(days):
    return timezone.localdate() - datetime.timedelta(days=days)


class Command(BaseCommand):
    help = "Load the TrustyHands demo data from the Figma designs."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true",
            help="Delete all existing TrustyHands data first.",
        )
        parser.add_argument(
            "--media-only", action="store_true",
            help="Only copy the demo pictures into your local media folder.",
        )

    # --- Entry point ---
    def handle(self, *args, **options):
        if options["media_only"]:
            self.restore_media()
            return
        random.seed(7)
        if User.objects.filter(email=f"admin@{DOMAIN}").exists():
            if not options["reset"]:
                raise CommandError(
                    "Demo data already exists. Use --reset to start again."
                )
            self.stdout.write("Deleting old data and demo pictures...")
            User.objects.all().delete()
            m.ServiceCategory.objects.all().delete()
            for folder in MEDIA_FOLDERS:
                shutil.rmtree(Path(settings.MEDIA_ROOT) / folder, ignore_errors=True)

        self.categories = self.create_categories()
        self.admin = self.create_admin()
        self.clients = self.create_clients()
        self.providers = self.create_providers()
        self.create_pending_providers()
        self.create_requests()
        self.create_extras()

        self.stdout.write(self.style.SUCCESS("Demo data loaded."))
        self.stdout.write(f"Password for every account: {PASSWORD}")
        self.stdout.write(f"  Admin:    admin@{DOMAIN}")
        self.stdout.write(f"  Provider: danny@{DOMAIN}")
        self.stdout.write(f"  Client:   chloe.kelly@{DOMAIN}")

    # --- Pictures for teammates (the database is shared, media is not) ---
    def restore_media(self):
        """
        Uploaded files live on the laptop that uploaded them. This writes
        the demo pictures into YOUR media folder, using the file names
        already saved in MongoDB.
        """
        by_name = {path.name: path for path in IMAGES.rglob("*") if path.is_file()}

        def find_source(saved_name):
            # Try the exact name, then the name without Django's suffix.
            base = Path(saved_name).name
            return by_name.get(base) or by_name.get(DJANGO_SUFFIX.sub("", base))

        media = Path(settings.MEDIA_ROOT)
        copied = 0
        for model in apps.get_app_config("core").get_models():
            file_fields = [
                f.name for f in model._meta.fields
                if isinstance(f, models.FileField)
            ]
            for record in model.objects.all() if file_fields else []:
                for field in file_fields:
                    name = getattr(record, field).name
                    if not name:
                        continue
                    target = media / name
                    source = find_source(name)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if source:
                        target.write_bytes(source.read_bytes())
                    elif name.endswith(".pdf"):
                        target.write_bytes(SAMPLE_PDF)
                    else:
                        continue
                    copied += 1
        for user in User.objects.exclude(profile_picture=""):
            name = user.profile_picture.name
            source = find_source(name)
            if source:
                target = media / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_bytes())
                copied += 1
        self.stdout.write(self.style.SUCCESS(f"{copied} pictures restored."))

    # --- Helpers ---
    def make_user(self, first, last, role, avatar=None, **extra):
        email = extra.pop(
            "email", f"{first}.{last}@{DOMAIN}".lower().replace(" ", "")
        )
        user = User(
            username=email, email=email, first_name=first, last_name=last,
            role=role, **extra,
        )
        user.set_password(PASSWORD)
        if avatar:
            user.profile_picture = image("avatars", avatar)
        user.save()
        return user

    # --- Categories (landing page cards) ---
    def create_categories(self):
        rows = [
            ("Master Carpentry", "carpentry", "TECHNICAL"),
            ("Expert Plumbing", "plumbing", "TECHNICAL"),
            ("Certified Electrician", "electrician", "TECHNICAL"),
            ("Precision Painting", "painting", "CREATIVE"),
            ("Interior Renovation", "interior", "CREATIVE"),
            ("Appliance Installation", "appliance", "TECHNICAL"),
        ]
        categories = {}
        for order, (name, key, group) in enumerate(rows):
            categories[key] = m.ServiceCategory.objects.create(
                name=name, slug=key, group=group, display_order=order,
                icon=image("categories", f"{key}.png"),
            )
        return categories

    # --- Admin ---
    def create_admin(self):
        return self.make_user(
            "Admin", "User", User.Role.ADMIN, avatar="admin.png",
            email=f"admin@{DOMAIN}", is_staff=True, is_superuser=True,
            phone="55500000",
        )

    # --- Clients (User Management and Active Jobs tables) ---
    def create_clients(self):
        rows = [
            ("Chloe", "Kelly", "chloe.png", "ACTIVE", "PLAINES_WILHEMS"),
            ("Reece", "James", "reece.png", "ACTIVE", "MOKA"),
            ("Tony", "Stark", "tony.png", "ACTIVE", "PORT_LOUIS"),
            ("Ollie", "Watkins", "ollie.png", "ACTIVE", "PLAINES_WILHEMS"),
            ("Chloe", "Evans", "chloe.png", "ACTIVE", "FLACQ"),
            ("Liam", "Davis", "liam.png", "DEACTIVATED", "MOKA"),
            ("Grace", "Kins", "grace.png", "SUSPENDED", "SAVANNE"),
            ("Noah", "Miller", "noah.png", "DEACTIVATED", "GRAND_PORT"),
            ("Sophia", "Thompson", "sophia.png", "ACTIVE", "BLACK_RIVER"),
            ("Jen", "Wilson", "jen.png", "ACTIVE", "PAMPLEMOUSSES"),
            ("Taylor", "Swift", "taylor.png", "SUSPENDED", "PORT_LOUIS"),
            ("Sarah", "John", None, "ACTIVE", "PLAINES_WILHEMS"),
            ("Ethan", "Harris", None, "ACTIVE", "MOKA"),
        ]
        clients = {}
        for index, (first, last, avatar, status, district) in enumerate(rows):
            user = self.make_user(
                first, last, User.Role.CLIENT, avatar=avatar,
                account_status=status, district=district,
                phone=f"5{7100000 + index * 131}",
                address=f"{10 + index} Royal Road",
            )
            user.last_login = timezone.now() - datetime.timedelta(days=index)
            user.save(update_fields=["last_login"])
            clients[f"{first} {last}"] = user
        return clients

    # --- Approved providers (Service Provider screen and dashboards) ---
    def create_providers(self):
        rows = [
            {
                "first": "Danny", "last": "Williams", "email": f"danny@{DOMAIN}",
                "business": "Danny Williams", "areas": ["PLAINES_WILHEMS", "MOKA"], "title": "Licensed Electrician",
                "town": "Castel", "district": "PLAINES_WILHEMS", "years": 15,
                "tier": "ELITE", "client_type": "RESIDENTIAL", "scale": "MEDIUM",
                "cover": "portfolio/panel_testing.png", "avatar": "danny.png",
                "categories": ["electrician", "plumbing"],
                "services": [
                    ("Wiring and Installations", "wiring.png", "electrician"),
                    ("Electronic Repairs", "repairs.png", "electrician"),
                ],
            },
            {
                "first": "David", "last": "Williams", "business": "David Williams", "areas": ["PLAINES_WILHEMS"],
                "title": "Licensed Electrician", "town": "Castel",
                "district": "PLAINES_WILHEMS", "years": 8, "tier": "STARTER",
                "client_type": "RESIDENTIAL", "scale": "SMALL",
                "cover": "providers/david_williams.png", "avatar": None,
                "categories": ["electrician"],
                "services": [
                    ("Wiring and Installations", "wiring.png", "electrician"),
                    ("Electronic Repairs", "repairs.png", "electrician"),
                ],
                "bio": (
                    "David has 8 years of experience on residential wiring in "
                    "Plaines Wilhems. He works alone, so every job is done by "
                    "him from the first visit to the final test."
                ),
                "specialisations": "Residential rewiring\nLighting\nFault finding",
                "specialty": (
                    "Full and partial rewiring of older houses, outdoor and "
                    "garden lighting, and finding faults that cause power cuts."
                ),
                "issues": (
                    "Power cuts when the kettle and iron run together: we "
                    "split the circuits and fit the right breaker.\n"
                    "Burnt smell from sockets: we replace damaged sockets and "
                    "check the cable behind them."
                ),
                "requirements": "Photos of the fuse board and the problem area help us quote.",
                "process": "Free first visit within Plaines Wilhems. Work is tested before we leave.",
                "portfolio": [
                    ("Outdoor Lighting for a Garden", "Priya R.", 35, "smart_fan.png"),
                    ("CCTV and Gate Wiring", "Kevin L.", 95, "cctv.png"),
                    ("Rewiring of a 1980s House", "Anjali D.", 160, "control_cabinet.png"),
                ],
            },
            {
                "first": "Marc", "last": "Jacobs", "business": "PowerLine Electricals", "areas": ["PLAINES_WILHEMS", "PORT_LOUIS", "MOKA"],
                "title": "Registered Contractor", "town": "Vacoas - Phoenix",
                "district": "PLAINES_WILHEMS", "years": 12, "tier": "PRO",
                "client_type": "BOTH", "scale": "LARGE",
                "cover": "providers/powerline.png", "avatar": None,
                "categories": ["electrician", "appliance"],
                "services": [
                    (
                        "Heavy Duty Electronic Equipment Installation",
                        "heavy_duty.png", "appliance",
                    ),
                    ("Safety Inspection and Report", "safety.png", "electrician"),
                ],
                "bio": (
                    "PowerLine is a team of six electricians working on shops, "
                    "offices and large homes. We install heavy equipment and "
                    "issue a written safety report after every job."
                ),
                "specialisations": "Commercial wiring\nThree-phase installation\nSafety reports",
                "specialty": (
                    "Three-phase supplies, distribution boards for shops and "
                    "offices, and safety inspections for insurance or sale."
                ),
                "issues": (
                    "Breakers tripping in a busy shop: we balance the load "
                    "across phases.\nOld boards with no earth leakage "
                    "protection: we upgrade the board and certify it."
                ),
                "requirements": "A site visit is needed for any commercial job. Please send the building plan if you have one.",
                "process": "Quote within 48 hours of the visit. Work outside opening hours on request.",
                "portfolio": [
                    ("Conduit Wiring for a Warehouse", "Bel Air Storage", 28, "conduit_wiring.png"),
                    ("Control Cabinet for a Bakery", "Boulangerie du Port", 76, "control_cabinet.png"),
                    ("Board Testing for an Office Block", "Ebene office block", 140, "panel_testing.png"),
                    ("Kitchen Appliance Circuits", "Hotel Sable", 210, "dishwasher.png"),
                ],
            },
            {
                "first": "Olivia", "last": "Perez", "business": "SolarVolt Solution", "areas": ["ISLAND_WIDE"],
                "title": "Registered Company", "town": "Island Wide",
                "district": "ISLAND_WIDE", "years": 6, "tier": "ELITE",
                "client_type": "BOTH", "scale": "LARGE",
                "cover": "providers/solarvolt.png", "avatar": None,
                "categories": ["electrician"],
                "services": [
                    ("Solar Energy Solutions", "solar.png", "electrician"),
                    ("EV Charger Installation", "ev.png", "electrician"),
                ],
                "bio": (
                    "SolarVolt designs and installs solar panels and home EV "
                    "chargers across Mauritius. We handle the CEB paperwork "
                    "and show you how to read your production each month."
                ),
                "specialisations": "Rooftop solar\nHome EV chargers\nBattery storage",
                "specialty": (
                    "Rooftop solar for homes and small businesses, wall "
                    "chargers for electric cars, and battery back-up."
                ),
                "issues": (
                    "Panels producing less than expected: we clean them and "
                    "check the inverter settings.\nCharger too slow: we check "
                    "the supply and move the charger to its own circuit."
                ),
                "requirements": "Send your last two electricity bills and a photo of the roof.",
                "process": "Roof survey, then a design with the expected savings. Installation in one to two days.",
                "portfolio": [
                    ("Solar Array for a Guest House", "Villa Corail", 22, "solarvolt.png"),
                    ("Inverter and Board for a 3 kW System", "Nitin P.", 64, "smart_panel.png"),
                    ("EV Charger Supply Cabling", "Claire M.", 150, "conduit_wiring.png"),
                ],
            },
            {
                "first": "Maria", "last": "Garcia", "business": "Garcia Handyman", "areas": ["PLAINES_WILHEMS", "BLACK_RIVER"],
                "title": "Registered Contractor", "town": "Quatre Bornes",
                "district": "PLAINES_WILHEMS", "years": 9, "tier": "PRO",
                "client_type": "RESIDENTIAL", "scale": "SMALL",
                "cover": "portfolio/house_paint.png", "avatar": None,
                "categories": ["carpentry", "painting", "interior"],
                "services": [
                    ("House Painting", None, "painting"),
                    ("Custom Furniture", None, "carpentry"),
                ],
                "bio": (
                    "Maria runs a small team of carpenters and painters in "
                    "Quatre Bornes. We build fitted furniture and repaint "
                    "rooms and facades, often in the same project."
                ),
                "specialisations": "Fitted wardrobes\nInterior painting\nSmall renovations",
                "specialty": (
                    "Made-to-measure wardrobes and kitchen cupboards, interior "
                    "and exterior painting, and small room makeovers."
                ),
                "issues": (
                    "Paint peeling after the rainy season: we treat the damp "
                    "and use a breathable paint.\nSwollen cupboard doors: we "
                    "replace them with moisture-resistant board."
                ),
                "requirements": "Room sizes or a quick sketch, and photos of the space.",
                "process": "Colour samples are painted on the wall before the job starts.",
                "portfolio": [
                    ("Repainting a Family House", "Elizabeth G.", 40, "house_paint.png"),
                    ("Bathroom Cabinet and Shelving", "Lisa J.", 120, "bathroom.png"),
                    ("Garage Door and Frame", "Emma L.", 185, "garage_door.png"),
                ],
            },
            {
                "first": "Harry", "last": "Styles", "business": "Styles Plumbing", "areas": ["PLAINES_WILHEMS", "GRAND_PORT", "SAVANNE"],
                "title": "Licensed Plumber", "town": "Curepipe",
                "district": "PLAINES_WILHEMS", "years": 11, "tier": "STARTER",
                "client_type": "BOTH", "scale": "MEDIUM",
                "cover": "portfolio/water_pipes.png", "avatar": None,
                "categories": ["plumbing"],
                "services": [
                    ("Pipe Leak Repair", None, "plumbing"),
                    ("Bathroom Renovation", None, "interior"),
                ],
                "bio": (
                    "Harry has 11 years of plumbing experience in Curepipe and "
                    "the central plateau. Most calls are leaks, water heaters "
                    "and bathroom refits."
                ),
                "specialisations": "Leak repair\nWater heaters\nBathroom refits",
                "specialty": (
                    "Finding and fixing leaks, installing solar and electric "
                    "water heaters, and full bathroom refits."
                ),
                "issues": (
                    "Low water pressure upstairs: we check the tank and fit a "
                    "pressure pump if needed.\nWater heater not heating: we "
                    "test the element and thermostat."
                ),
                "requirements": "Tell us where the leak is and how long it has been there.",
                "process": "Emergency calls answered the same day in Curepipe.",
                "portfolio": [
                    ("Leak Repair Under a Kitchen Sink", "Ravi S.", 18, "water_pipes.png"),
                    ("Dishwasher Plumbing", "Sandra T.", 70, "dishwasher.png"),
                    ("Full Bathroom Refit", "Yan C.", 175, "bathroom.png"),
                ],
            },
        ]
        # Approved at different times, so "Approvals" has a real history.
        verified_ages = [210, 150, 95, 40, 18, 6]
        providers = {}
        for index, row in enumerate(rows):
            verified_age = verified_ages[index]
            user = self.make_user(
                row["first"], row["last"], User.Role.PROVIDER,
                avatar=row["avatar"], district=row["district"],
                phone=f"5{7123412 + index}",
                **({"email": row["email"]} if "email" in row else {}),
            )
            folder, cover = row["cover"].split("/")
            provider = m.ServiceProvider.objects.create(
                user=user, business_name=row["business"],
                profession_title=row["title"], town=row["town"],
                district=row["district"], years_experience=row["years"],
                client_type=row["client_type"], project_scale=row["scale"],
                cover_photo=image(folder, cover),
                areas_served=row["areas"],
                verification_status="APPROVED",
                verification_stage="INSURANCE",
                submitted_at=timezone.now()
                - datetime.timedelta(days=verified_age + 6),
                verified_at=timezone.now() - datetime.timedelta(days=verified_age),
                bio=row.get("bio", ""),
                main_specializations=row.get("specialisations", ""),
                specialty_areas=row.get("specialty", ""),
                common_issues=row.get("issues", ""),
                service_requirements=row.get("requirements", (
                    "A preliminary site description and service request are "
                    "needed for an accurate quote."
                )),
                process_notes=row.get("process", "On-site checks are mandatory."),
                bank_name="MCB" if index % 2 == 0 else "SBM",
                bank_account_number=f"0001{23450000 + index * 1111}",
            )
            for stage in ["IDENTITY", "BACKGROUND", "LICENSE", "INSURANCE"]:
                m.VerificationLog.objects.create(
                    provider=provider, admin=self.admin,
                    action=m.VerificationLog.Action.STAGE, stage=stage,
                )
            log = m.VerificationLog.objects.create(
                provider=provider, admin=self.admin,
                action=m.VerificationLog.Action.APPROVE,
                note="All documents checked.",
            )
            backdate(log, created_at=provider.verified_at)
            m.VerificationLog.objects.filter(
                provider=provider, action=m.VerificationLog.Action.STAGE
            ).update(created_at=provider.verified_at - datetime.timedelta(days=2))
            provider.categories.set(
                [self.categories[key] for key in row["categories"]]
            )
            for name, icon, category in row["services"]:
                m.ProviderService.objects.create(
                    provider=provider, name=name,
                    category=self.categories[category],
                    icon=image("services", icon) if icon else "",
                )
            m.Subscription.objects.create(provider=provider, tier=row["tier"])
            # One subscription payment per month since the provider joined.
            if row["tier"] != "STARTER":
                for month in range(min(verified_age // 30 + 1, 7)):
                    payment = m.Payment.objects.create(
                        provider=provider, tier=row["tier"],
                        billing_cycle="MONTHLY",
                        amount=m.Subscription.price_for(row["tier"], "MONTHLY"),
                        reference=f"PAY-{1000 + index * 10 + month}",
                    )
                    backdate(payment, created_at=timezone.now()
                             - datetime.timedelta(days=month * 30 + index + 1))
            for kind, doc_type in [
                ("license", "LICENSE"), ("certification", "CERTIFICATION"),
                ("insurance", "INSURANCE"), ("brn", "BRN"),
            ]:
                filename = f"{slug(row['business'])}_{kind}.pdf"
                doc = m.VerificationDocument.objects.create(
                    provider=provider, doc_type=doc_type, name=filename,
                    verification_status="APPROVED", file=document(filename),
                )
                backdate(doc, uploaded_at=provider.submitted_at)
            for title, client_name, age, photo in row.get("portfolio", []):
                folder_name = "providers" if photo == "solarvolt.png" else "portfolio"
                m.PortfolioItem.objects.create(
                    provider=provider, title=title, client_name=client_name,
                    completed_on=days_ago(age), photo=image(folder_name, photo),
                    description=f"{title} for {client_name}.",
                )
            m.ScheduleSettings.objects.create(
                provider=provider,
                services_offered=["PLUMBING", "MAINTENANCE", "REPAIRS",
                                  "INSTALLATION"],
            )
            providers[row["business"]] = provider

        # Extra details for Danny, the demo provider account.
        danny = providers["Danny Williams"]
        danny.bio = (
            "With over 15 years of professional experience, Danny is a "
            "dedicated and fully licensed electrician. He specializes in smart "
            "home integration, energy-sufficient lighting, and intricate "
            "commercial wiring, with a focus on safety, precision, and "
            "reliable customer service."
        )
        danny.main_specializations = (
            "Residential Plumbing\nSmart Home Integration\n"
            "Domestic Electrical Work"
        )
        danny.specialty_areas = (
            "Smart home integration, energy-efficient lighting and "
            "commercial wiring."
        )
        danny.common_issues = (
            "Tripping breakers: we check the load and replace faulty "
            "breakers.\nFlickering lights: we test the wiring and fixtures."
        )
        danny.service_requirements = (
            "A short description of the problem and a photo of the fuse "
            "board or pipes help us give an accurate quote."
        )
        danny.process_notes = (
            "On-site check first. The quote is sent the same day and work "
            "starts once you accept it."
        )
        danny.bank_name = "MCB"
        danny.bank_account_number = "000123454321"
        danny.save()
        return providers

    # --- Pending providers (Verification Queue) ---
    def create_pending_providers(self):
        rows = [
            ("Zara", "Carter", "Plumber", "plumbing", "BACKGROUND", 3, "Saint Pierre", 4),
            ("Adrian", "Wilson", "Carpenter", "carpentry", "BACKGROUND", 9, "Moka", 7),
            ("Kiara", "Patel", "Electrician", "electrician", "BACKGROUND", 15, "Rose Belle", 2),
            ("Noah", "Bennet", "Carpenter", "carpentry", "IDENTITY", 24, "Goodlands", 12),
            ("Maya", "Reynolds", "Painter", "painting", "LICENSE", 33, "Flacq", 5),
            ("Ryan", "Wilson", "Electrician", "electrician", "BACKGROUND", 41, "Beau Bassin", 9),
            ("Ava", "Milton", "Plumber", "plumbing", "INSURANCE", 52, "Mahebourg", 3),
        ]
        for first, last, title, category, stage, age, town, years in rows:
            user = self.make_user(first, last, User.Role.PROVIDER)
            provider = m.ServiceProvider.objects.create(
                user=user, business_name=f"{first} {last}",
                profession_title=title, district="MOKA", town=town,
                verification_stage=stage, years_experience=years,
                submitted_at=timezone.now() - datetime.timedelta(days=age),
                bio=(
                    f"{title} based in {town} with {years} years of "
                    "experience, now taking on new clients."
                ),
            )
            provider.categories.set([self.categories[category]])
            m.Subscription.objects.create(provider=provider)
            name = f"{first} {last}"
            for kind, doc_type in [("brn", "BRN"), ("license", "LICENSE")]:
                filename = f"{slug(name)}_{kind}.pdf"
                doc = m.VerificationDocument.objects.create(
                    provider=provider, doc_type=doc_type, name=filename,
                    file=document(filename),
                )
                backdate(doc, uploaded_at=provider.submitted_at)

    # --- Service requests, reviews and earnings ---
    def create_requests(self):
        danny = self.providers["Danny Williams"]
        plumbing = self.categories["plumbing"]
        electrician = self.categories["electrician"]
        now = timezone.now()

        def request(client, provider, status, days, created_days_ago=None, **extra):
            client = self.clients[client]
            defaults = {
                "category": plumbing,
                "job_type": JobType.PLUMBING,
                "description": "Expert Plumbing",
                "contact_name": client.display_name,
                "contact_phone": client.phone,
                "contact_email": client.email,
                "location": client.address,
            }
            defaults.update(extra)
            created = m.ServiceRequest.objects.create(
                client=client, provider=provider, status=status,
                preferred_date=timezone.localdate()
                + datetime.timedelta(days=days),
                **defaults,
            )
            # Requests were sent before their preferred date, not all today.
            if created_days_ago is None:
                created_days_ago = max(-days, 0) + random.randint(2, 9)
            backdate(created, created_at=now - datetime.timedelta(
                days=created_days_ago, hours=random.randint(0, 10)))
            return created

        def complete(job, age, rating=None):
            job.completed_at = now - datetime.timedelta(days=age)
            job.save(update_fields=["completed_at"])
            rating = rating or stars()
            review = m.Review.objects.create(
                request=job, client=job.client, provider=job.provider,
                rating=rating, comment=comment_for(rating),
            )
            backdate(review, created_at=job.completed_at
                     + datetime.timedelta(days=random.randint(0, 3)))

        # Active jobs (In Progress)
        for name, days in [
            ("Chloe Kelly", -3), ("Reece James", 1),
            ("Tony Stark", 2), ("Ollie Watkins", 2),
        ]:
            request(name, danny, "IN_PROGRESS", days)

        # New job requests queue (Pending)
        request("Chloe Kelly", danny, "PENDING", 4, created_days_ago=1,
                description="Leaking Faucet", urgency="HIGH")
        request("Tony Stark", danny, "PENDING", 6, created_days_ago=2,
                description="Pipe Leak Repair", job_type="REPAIRS")
        request("Ollie Watkins", danny, "PENDING", 8, created_days_ago=3,
                description="Toilet Repair", job_type="REPAIRS")

        # Upcoming bookings (Scheduled)
        request("Sophia Thompson", danny, "ACCEPTED", 5,
                description="Water Heater Repair", job_type="REPAIRS")
        request("Jen Wilson", danny, "ACCEPTED", 9,
                description="Shower Installation", job_type="INSTALLATION")

        # Danny's completed jobs: earnings history and reviews (FR 6.1).
        # He works in both electrical and plumbing jobs.
        history = [
            ("Chloe Evans", 2, "1850", "INSTALLATION", "Elec. Install", "electrician"),
            ("Sophia Thompson", 4, "950", "REPAIRS", "Elec. Repair", "electrician"),
            ("Sarah John", 8, "450", "MAINTENANCE", "Maintenance", "plumbing"),
            ("Ethan Harris", 15, "250", "REPAIRS", "Tap Replacement", "plumbing"),
            ("Jen Wilson", 20, "600", "REPAIRS", "Elec. Repairs", "electrician"),
            ("Reece James", 25, "800", "INSTALLATION", "Elec. Install", "electrician"),
            ("Tony Stark", 40, "1200", "REPAIRS", "Pipe Repair", "plumbing"),
            ("Ollie Watkins", 70, "2400", "INSTALLATION", "Panel Upgrade", "electrician"),
            ("Chloe Kelly", 100, "1600", "MAINTENANCE", "Maintenance", "plumbing"),
            ("Sarah John", 130, "2800", "INSTALLATION", "Rewiring", "electrician"),
            ("Ethan Harris", 160, "900", "REPAIRS", "Elec. Repair", "electrician"),
            ("Jen Wilson", 190, "1150", "INSTALLATION", "Elec. Install", "electrician"),
        ]
        # Danny is the demo account, so his ratings are fixed (average 4.6).
        danny_ratings = [5, 5, 4, 5, 5, 3, 5, 4, 5, 5, 4, 5]
        for index, (name, age, amount, job_type, text, category) in enumerate(history):
            job = request(
                name, danny, "COMPLETED", -age,
                category=self.categories[category],
                job_type=job_type, description=text,
                final_amount=Decimal(amount),
                payout_status="PENDING" if index < 2 else "PAID",
            )
            complete(job, age, danny_ratings[index])

        # Other providers: completed jobs in their own categories, spread
        # over the last eight months, with amounts that are not round.
        active_clients = [
            name for name, user in self.clients.items()
            if user.account_status == "ACTIVE"
        ]
        jobs_by_provider = {
            "David Williams": (7, ["electrician"], ["Socket Repair", "Rewiring", "Light Fitting"]),
            "PowerLine Electricals": (9, ["electrician", "appliance"], ["Board Upgrade", "Three-phase Supply", "Oven Installation", "Safety Report"]),
            "SolarVolt Solution": (6, ["electrician"], ["Solar Install", "EV Charger", "Inverter Check"]),
            "Garcia Handyman": (8, ["carpentry", "painting", "interior"], ["Wardrobe Build", "Room Painting", "Kitchen Cupboards", "Facade Painting"]),
            "Styles Plumbing": (7, ["plumbing", "interior"], ["Leak Repair", "Water Heater", "Bathroom Refit", "Pump Install"]),
        }
        for business, (count, category_keys, jobs) in jobs_by_provider.items():
            provider = self.providers[business]
            for index in range(count):
                age = random.randint(3, 240)
                category = self.categories[random.choice(category_keys)]
                job = request(
                    random.choice(active_clients), provider, "COMPLETED", -age,
                    category=category,
                    job_type=random.choice(["INSTALLATION", "REPAIRS", "MAINTENANCE"]),
                    description=random.choice(jobs),
                    final_amount=Decimal(random.randrange(350, 4800, 25)),
                    payout_status="PAID",
                )
                complete(job, age)
            provider.recalculate_completed_jobs()

        # Open, declined and cancelled requests in recent weeks, so the
        # admin tables and the "Requests per week" chart look lived-in.
        recent = [
            ("Sarah John", "PowerLine Electricals", "IN_PROGRESS", 1, "electrician", "Board Upgrade"),
            ("Ethan Harris", "Styles Plumbing", "IN_PROGRESS", -2, "plumbing", "Water Heater"),
            ("Jen Wilson", "David Williams", "PENDING", 3, "electrician", "Socket Repair"),
            ("Reece James", "Garcia Handyman", "ACCEPTED", 6, "painting", "Room Painting"),
            ("Sophia Thompson", "SolarVolt Solution", "PENDING", 10, "electrician", "Solar Install"),
            ("Chloe Evans", "Garcia Handyman", "DECLINED", -12, "carpentry", "Wardrobe Build"),
            ("Tony Stark", "Styles Plumbing", "CANCELLED", -20, "plumbing", "Pump Install"),
            ("Ollie Watkins", "PowerLine Electricals", "ACCEPTED", 12, "appliance", "Oven Installation"),
            ("Chloe Kelly", "Garcia Handyman", "PENDING", 7, "interior", "Kitchen Cupboards"),
        ]
        for name, business, status, days, category, text in recent:
            request(name, self.providers[business], status, days,
                    created_days_ago=random.randint(1, 50),
                    category=self.categories[category], description=text)
        danny.recalculate_completed_jobs()

    # --- Portfolio, schedule, payouts, notifications, wishlist ---
    def create_extras(self):
        danny = self.providers["Danny Williams"]
        projects = [
            ("Installation of Dishwasher", "Elizabeth G.", 50, "dishwasher.png"),
            ("Water Pipes Leakage", "Elizabeth H.", 80, "water_pipes.png"),
            ("Installation of Smart Home Fan", "Sam I.", 110, "smart_fan.png"),
            ("Renovation of bathroom cabinet+ bathtub", "Lisa J.", 115,
             "bathroom.png"),
            ("Smart-panel Installation", "Danny K.", 140, "smart_panel.png"),
            ("Installtion of Automatic Garage Door", "Emma L.", 145,
             "garage_door.png"),
            ("House Paintjob", "Elizabeth G.", 200, "house_paint.png"),
            ("Installation of CCTV system", "Fred W.", 230, "cctv.png"),
            ("Distribution Board Testing", "Kevin P.", 260, "panel_testing.png"),
            ("Control Cabinet Wiring", "Nadia R.", 300, "control_cabinet.png"),
            ("Industrial Conduit Wiring", "Anil S.", 330, "conduit_wiring.png"),
        ]
        for title, client_name, age, photo in projects:
            m.PortfolioItem.objects.create(
                provider=danny, title=title, client_name=client_name,
                completed_on=days_ago(age), photo=image("portfolio", photo),
                description=f"{title} for {client_name}",
            )

        today = timezone.localdate()
        m.BlockedDate.objects.create(
            provider=danny, start_date=today + datetime.timedelta(days=12),
            end_date=today + datetime.timedelta(days=14), reason="Family leave",
        )
        m.BlockedTime.objects.create(
            provider=danny, label="Lunch Break",
            start_time=datetime.time(12, 0), end_time=datetime.time(13, 0),
        )

        # TrustyHands does not hold money, so there are no payouts to seed.

        # Profile visits for every approved provider, not only Danny.
        visits = {
            "Danny Williams": 215, "David Williams": 64,
            "PowerLine Electricals": 131, "SolarVolt Solution": 158,
            "Garcia Handyman": 89, "Styles Plumbing": 47,
        }
        for business, count in visits.items():
            for _ in range(count):
                view = m.ProfileView.objects.create(
                    provider=self.providers[business]
                )
                view.viewed_at = timezone.now() - datetime.timedelta(
                    days=random.randint(0, 29), hours=random.randint(0, 23)
                )
                view.save(update_fields=["viewed_at"])

        m.Notification.objects.create(
            user=danny.user, title="New job request",
            message="Chloe Kelly sent you a request: Leaking Faucet.",
            link="/provider/dashboard/",
        )
        m.Notification.objects.create(
            user=danny.user, title="Profile verified",
            message="Your profile was approved by the TrustyHands team.",
            is_read=True,
        )

        chloe = self.clients["Chloe Kelly"]
        for business in ["Danny Williams", "SolarVolt Solution"]:
            m.WishlistItem.objects.create(
                client=chloe, provider=self.providers[business]
            )
