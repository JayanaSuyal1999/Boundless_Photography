# Boundless Moments Photography — Flask + PostgreSQL

## Project Structure

```
boundless_flask/
├── app.py                  ← Flask routes & API endpoints
├── models.py               ← SQLAlchemy database models
├── requirements.txt
├── .env                    ← Environment variables (edit before running)
│
├── templates/
│   ├── base.html           ← Shared layout (nav + footer)
│   ├── index.html          ← Home page
│   └── pages/
│       ├── portfolio.html  ← Gallery with filters
│       ├── skills.html     ← Team, skills, awards
│       ├── contact.html    ← Contact form
│       └── admin.html      ← Admin dashboard
│
└── static/
    ├── css/
    │   ├── style.css       ← Global tokens, reset, nav, footer
    │   ├── home.css        ← Home page styles
    │   ├── portfolio.css   ← Gallery & lightbox styles
    │   ├── skills.css      ← Team cards & award cards
    │   ├── contact.css     ← Contact form styles
    │   └── admin.css       ← Admin dashboard styles
    ├── js/
    │   ├── main.js         ← Global (nav, fade-up, cursor glow)
    │   ├── portfolio.js    ← Lightbox
    │   ├── skills.js       ← Skill bar animation
    │   ├── contact.js      ← Form submission to /api/contact
    │   └── admin.js        ← Dashboard CRUD & API calls
    └── images/             ← Upload portfolio images here
```

---

## Database Tables (PostgreSQL)

| Table            | Description                                      | Key Relationships              |
|------------------|--------------------------------------------------|-------------------------------|
| `admin_users`    | Admin login credentials (hashed passwords)       | —                             |
| `portfolio_items`| Portfolio projects (title, category, year)       | Has many `gallery_images`     |
| `gallery_images` | Images belonging to a portfolio item             | Belongs to `portfolio_items`  |
| `team_members`   | Photographer profiles                            | Has many `skills`             |
| `skills`         | Individual skill bars for each team member       | Belongs to `team_members`     |
| `awards`         | Awards and recognitions                          | —                             |
| `messages`       | Contact form submissions                         | —                             |
| `site_content`   | Key-value store for editable website copy        | —                             |

---

## Setup & Run

### 1. Create a PostgreSQL database
```sql
CREATE DATABASE boundless_moments;
```

### 2. Configure environment variables
Edit `.env`:
```
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/boundless_moments
ADMIN_USERNAME=admin
ADMIN_PASSWORD=boundless2026
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Create tables & seed data
```bash
flask init-db
```
This creates all 8 tables and seeds:
- 1 admin user
- 12 portfolio items
- 3 team members + 9 skills
- 8 awards
- Default site content

### 5. Run the development server
```bash
flask run
```
Visit: http://127.0.0.1:5000

---

## Admin Panel
- URL: http://127.0.0.1:5000/admin
- Default login: `admin` / `boundless2026`
- Features: portfolio CRUD, message inbox, site content editor

## API Endpoints

| Method | Endpoint                              | Description                   |
|--------|---------------------------------------|-------------------------------|
| POST   | `/api/contact`                        | Submit contact form           |
| POST   | `/admin/login`                        | Admin login                   |
| GET    | `/api/admin/portfolio`               | List all portfolio items      |
| POST   | `/api/admin/portfolio`               | Create portfolio item         |
| PUT    | `/api/admin/portfolio/<id>`          | Update portfolio item         |
| DELETE | `/api/admin/portfolio/<id>`          | Delete portfolio item         |
| GET    | `/api/admin/messages`                | List all messages             |
| PATCH  | `/api/admin/messages/<id>/read`      | Mark message as read          |
| DELETE | `/api/admin/messages/<id>`           | Delete message                |
| GET    | `/api/admin/content`                 | Get site content settings     |
| POST   | `/api/admin/content`                 | Update site content settings  |
