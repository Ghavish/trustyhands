# TrustyHands — Home Services & Tradesperson Platform

Welcome to the official repository for **TrustyHands**, a comprehensive, secure, and modern platform connecting homeowners with vetted, high-quality home service professionals and tradespeople. 

This repository houses the complete documentation, design assets, and functional frontend/backend structural components developed for academic coursework and platform prototyping.

---

## 🚀 Project Overview & Vision
TrustyHands bridges the gap between reliable homeowners and skilled professionals (plumbers, electricians, carpenters, painters, and HVAC technicians) by introducing full transparency, verified background checks, automated scheduling, and real-time job tracking.

### Core User Roles
1. **Clients:** Can browse verified service categories, check detailed professional portfolios (with ratings, credentials, and past work), book appointments via an integrated calendar, and manage active service requests.
2. **Service Providers:** Can onboard via a streamlined multi-step portfolio and verification hub, subscribe to partner tiers, manage incoming job requests, organize their weekly availability, and track lifetime earnings.
3. **Admin:** Have complete oversight via a high-level analytics dashboard, verification queue management tools, user account controls, and dispute mediation workflows.

---

## 🛠️ Technology Stack & Architecture
* **Frontend Design & Prototyping:** Figma (light and dark mode, custom colour palette).
* **Web Application Architecture:**
 * **Framework:** Django 6.1 (Python 3.12 or newer)
 * **Database:** MongoDB Atlas, connected with `django-mongodb-backend`
 * **Pages:** Django templates, plain CSS and JavaScript, Chart.js for dashboard charts
 * **Languages:** English and French (Django translations)
## Getting Started
1. Clone the repository and open the folder.
2. Create a virtual environment and install the packages:
 `python -m venv venv`, activate it, then `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and paste the MongoDB Atlas connection string.
4. Run `python manage.py migrate`, then `python manage.py seed_demo` for demo data.
5. Start the site with `python manage.py runserver` and open http://127.0.0.1:8000

## ✨ Key Features & Screen Workflows

### 🏠 Client Experience
* **Landing Page:** High-converting hero section with direct category lookups and trust signals.
* **Professional Directory:** Filterable grid of certified experts categorized by trade.
* **Detailed Portfolio Views:** Immersive profiles showcasing past project highlights, certifications, and verified client testimonials.
* **Booking & Scheduling Flow:** Seamless date selection and issue description form for instant service requests.

### 🔧 Service Provider Workspace
* **Onboarding & Subscription Hub:** Multi-step registration allowing professionals to upload project blueprints, technical specs, and select membership tiers (**Starter (Free)**, **Pro Partner (MUR 500/mo)**, and **Elite Master (MUR 1,000/mo)**).
* **Operational Dashboard:** 
  * *Active Jobs & Requests:* Real-time tracking of jobs in progress and urgent incoming client requests.
  * *Schedule Manager:* Interactive calendar tool for managing availability and blocking out dates.
  * *Portfolio Editor:* Backend management tool for updating service offerings, licenses, and project showcases.
  * *Earnings Overview:* Financial tracking including lifetime earnings, payout schedules, and tax document access.

### 🛡️ Admin Control Panel
* **Verification Queue:** Streamlining background checks, license approvals, and insurance validation.
* **User Management:** Granular controls for suspending, restoring, or modifying client and provider permissions.
* **Service Requests Oversight:** End-to-end monitoring of job statuses ranging from pending approval to disputed mediation.

---

## 👥 Team & Contributions
Developed collaboratively as part of academic engineering and software development modules at the University of Mauritius.

* **Project Lead & Architecture:** Ghavish Subratty
* **Platform Design & Development:** Team *Git Happens*

---

## 📄 License
This project is developed for educational and portfolio presentation purposes under standard institutional guidelines.