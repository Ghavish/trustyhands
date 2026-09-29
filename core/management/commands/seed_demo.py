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
                "business": "Danny Williams", "title": "Licensed Electrician",
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
                "first": "David", "last": "Williams", "business": "David Williams",
                "title": "Licensed Electrician", "town": "Castel",
                "district": "PLAINES_WILHEMS", "years": 8, "tier": "STARTER",
                "client_type": "RESIDENTIAL", "scale": "SMALL",
                "cover": "providers/david_williams.png", "avatar": None,
                "categories": ["electrician"],
                "services": [
                    ("Wiring and Installations", "wiring.png", "electrician"),
                    ("Electronic Repairs", "repairs.png", "electrician"),
                ],
            },
            {
                "first": "Marc", "last": "Jacobs", "business": "PowerLine Electricals",
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
            },
            {
                "first": "Olivia", "last": "Perez", "business": "SolarVolt Solution",
                "title": "Registered Company", "town": "Island Wide",
                "district": "ISLAND_WIDE", "years": 6, "tier": "ELITE",
                "client_type": "BOTH", "scale": "LARGE",
                "cover": "providers/solarvolt.png", "avatar": None,
                "categories": ["electrician"],
                "services": [
                    ("Solar Energy Solutions", "solar.png", "electrician"),
                    ("EV Charger Installation", "ev.png", "electrician"),
                ],
            },
            {
                "first": "Maria", "last": "Garcia", "business": "Garcia Handyman",
                "title": "Registered Contractor", "town": "Quatre Bornes",
                "district": "PLAINES_WILHEMS", "years": 9, "tier": "PRO",
                "client_type": "RESIDENTIAL", "scale": "SMALL",
                "cover": "portfolio/house_paint.png", "avatar": None,
                "categories": ["carpentry", "painting", "interior"],
                "services": [
                    ("House Painting", None, "painting"),
                    ("Custom Furniture", None, "carpentry"),
                ],
            },
            {
                "first": "Harry", "last": "Styles", "business": "Styles Plumbing",
                "title": "Licensed Plumber", "town": "Curepipe",
                "district": "PLAINES_WILHEMS", "years": 11, "tier": "STARTER",
                "client_type": "BOTH", "scale": "MEDIUM",
                "cover": "portfolio/water_pipes.png", "avatar": None,
                "categories": ["plumbing"],
                "services": [
                    ("Pipe Leak Repair", None, "plumbing"),
                    ("Bathroom Renovation", None, "interior"),
                ],
            },
        ]
        providers = {}
        for index, row in enumerate(rows):
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
                areas_served=[row["district"], "MOKA"],
                verification_status="APPROVED",
                verification_stage="INSURANCE",
                submitted_at=timezone.now() - datetime.timedelta(days=90),
                verified_at=timezone.now() - datetime.timedelta(days=80),
                bio=(
                    f"With over {row['years']} years of professional "
                    "experience, we deliver safe, precise and reliable work "
                    "with a focus on customer service."
                ),
                service_requirements=(
                    "A preliminary site description and service request are "
                    "needed for an accurate quote."
                ),
                process_notes="On-site checks are mandatory.",
            )
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
            if row["tier"] != "STARTER":
                m.Payment.objects.create(
                    provider=provider, tier=row["tier"],
                    billing_cycle="MONTHLY",
                    amount=m.Subscription.price_for(row["tier"], "MONTHLY"),
                    reference=f"PAY-{1000 + index}",
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
        danny.bank_name = "MCB"
        danny.bank_account_number = "000123454321"
        danny.save()
        return providers

    # --- Pending providers (Verification Queue) ---
    def create_pending_providers(self):
        rows = [
            ("Zara", "Carter", "Plumber", "plumbing", "BACKGROUND", 0),
            ("Adrian", "Wilson", "Carpenter", "carpentry", "BACKGROUND", 2),
            ("Kiara", "Patel", "Electrician", "electrician", "BACKGROUND", 9),
            ("Noah", "Bennet", "Carpenter", "carpentry", "IDENTITY", 14),
            ("Maya", "Reynolds", "Painter", "painting", "LICENSE", 0),
            ("Ryan", "Wilson", "Electrician", "electrician", "BACKGROUND", 5),
            ("Ava", "Milton", "Plumber", "plumbing", "INSURANCE", 10),
        ]
        for first, last, title, category, stage, age in rows:
            user = self.make_user(first, last, User.Role.PROVIDER)
            provider = m.ServiceProvider.objects.create(
                user=user, business_name=f"{first} {last}",
                profession_title=title, district="MOKA",
                verification_stage=stage, years_experience=4,
                submitted_at=timezone.now() - datetime.timedelta(days=age),
                bio=f"{title} with 4 years of experience.",
            )
            provider.categories.set([self.categories[category]])
            m.Subscription.objects.create(provider=provider)
            m.VerificationDocument.objects.create(
                provider=provider, doc_type="BRN",
                name=f"{first.lower()}_brn.pdf",
                file=ContentFile(SAMPLE_PDF, name=f"{first.lower()}_brn.pdf"),
            )

    # --- Service requests, reviews and earnings ---
    def create_requests(self):
        danny = self.providers["Danny Williams"]
        plumbing = self.categories["plumbing"]
        electrician = self.categories["electrician"]

        def request(client, provider, status, days, **extra):
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
            return created

        # Active jobs (In Progress)
        for name, days in [
            ("Chloe Kelly", -3), ("Reece James", 1),
            ("Tony Stark", 2), ("Ollie Watkins", 2),
        ]:
            request(name, danny, "IN_PROGRESS", days)

        # New job requests queue (Pending)
        request("Chloe Kelly", danny, "PENDING", 4,
                description="Leaking Faucet", urgency="HIGH")
        request("Tony Stark", danny, "PENDING", 6,
                description="Pipe Leak Repair", job_type="REPAIRS")
        request("Ollie Watkins", danny, "PENDING", 8,
                description="Toilet Repair", job_type="REPAIRS")

        # Upcoming bookings (Scheduled)
        request("Sophia Thompson", danny, "ACCEPTED", 5,
                description="Water Heater Repair", job_type="REPAIRS")
        request("Jen Wilson", danny, "ACCEPTED", 9,
                description="Shower Installation", job_type="INSTALLATION")

        # Completed jobs: earnings history and reviews (FR 6.1)
        history = [
            ("Chloe Evans", 2, "1850", "INSTALLATION", "Elec. Install", 5),
            ("Sophia Thompson", 4, "950", "REPAIRS", "Elec. Repair", 5),
            ("Sarah John", 8, "450", "MAINTENANCE", "Maintenance", 4),
            ("Ethan Harris", 15, "250", "INSTALLATION", "Elec. Install", 5),
            ("Jen Wilson", 20, "600", "REPAIRS", "Elec. Repairs", 5),
            ("Reece James", 25, "800", "INSTALLATION", "Elec. Install", 5),
            ("Tony Stark", 40, "1200", "REPAIRS", "Pipe Repair", 5),
            ("Ollie Watkins", 70, "2400", "INSTALLATION", "Panel Upgrade", 4),
            ("Chloe Kelly", 100, "1600", "MAINTENANCE", "Maintenance", 5),
            ("Sarah John", 130, "2800", "INSTALLATION", "Rewiring", 5),
            ("Ethan Harris", 160, "900", "REPAIRS", "Elec. Repair", 5),
            ("Jen Wilson", 190, "1150", "INSTALLATION", "Elec. Install", 5),
        ]
        for index, (name, age, amount, job_type, text, stars) in enumerate(
            history
        ):
            job = request(
                name, danny, "COMPLETED", -age, category=electrician,
                job_type=job_type, description=text,
                final_amount=Decimal(amount),
                payout_status="PENDING" if index < 2 else "PAID",
            )
            job.completed_at = timezone.now() - datetime.timedelta(days=age)
            job.save(update_fields=["completed_at"])
            m.Review.objects.create(
                request=job, client=job.client, provider=danny,
                rating=stars,
                comment="Professional, on time and very clean work.",
            )

        # Other providers: a few completed jobs so they have ratings.
        for business, ratings in [
            ("David Williams", [5, 5, 4, 5]),
            ("PowerLine Electricals", [5, 4, 5, 5, 4]),
            ("SolarVolt Solution", [5, 5, 5, 5]),
            ("Garcia Handyman", [5, 4, 4]),
            ("Styles Plumbing", [4, 5]),
        ]:
            provider = self.providers[business]
            for index, stars in enumerate(ratings):
                job = request(
                    list(self.clients)[index], provider, "COMPLETED",
                    -(10 + index * 7), category=electrician,
                    job_type="INSTALLATION", description="Installation",
                    final_amount=Decimal(500 + index * 150),
                )
                job.completed_at = timezone.now() - datetime.timedelta(
                    days=10 + index * 7
                )
                job.save(update_fields=["completed_at"])
                m.Review.objects.create(
                    request=job, client=job.client, provider=provider,
                    rating=stars, comment="Great service.",
                )
            provider.recalculate_completed_jobs()

        # Requests shown in the admin Service Requests table
        request("Sarah John", self.providers["PowerLine Electricals"],
                "IN_PROGRESS", 1, category=plumbing)
        request("Ethan Harris", self.providers["Styles Plumbing"],
                "IN_PROGRESS", -2, description="Painting")
        request("Liam Davis", self.providers["David Williams"],
                "PENDING", 3, category=electrician)
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

        for doc_type, name in [
            ("LICENSE", "license_masterelectrician.pdf"),
            ("CERTIFICATION", "4628362025.pdf"),
            ("BRN", "greencompanyid7824.pdf"),
        ]:
            m.VerificationDocument.objects.create(
                provider=danny, doc_type=doc_type, name=name,
                verification_status="APPROVED",
                file=ContentFile(SAMPLE_PDF, name=name),
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

        for amount, age in [("3200", 60), ("2100", 30)]:
            m.Payout.objects.create(
                provider=danny, amount=Decimal(amount), status="PAID",
                bank_label=danny.bank_label,
                paid_at=timezone.now() - datetime.timedelta(days=age),
            )

        for _ in range(215):
            view = m.ProfileView.objects.create(provider=danny)
            view.viewed_at = timezone.now() - datetime.timedelta(
                days=random.randint(0, 29)
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
