# app.py — Boundless Moments Photography
# Flask application entry point with all routes and API endpoints.

import os
import uuid
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from models import db, AdminUser, PortfolioItem, GalleryImage, TeamMember, Skill, Award, Message, SiteContent
from datetime import date

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ── Load environment variables ────────────────────────────────────────────────
load_dotenv()

# ── App factory ───────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"]           = os.getenv("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:yourpassword@localhost:5432/boundless_moments"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "images")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload

# ── Extensions ────────────────────────────────────────────────────────────────
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "admin_login"

@login_manager.user_loader
def load_user(user_id):
    return AdminUser.query.get(int(user_id))


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC PAGE ROUTES
# Each route fetches its data from PostgreSQL and passes it to a Jinja template.
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    """Home page — featured portfolio items + testimonials."""
    featured = PortfolioItem.query.filter_by(featured=True).order_by(PortfolioItem.sort_order).limit(5).all()
    content  = {
        "tagline": SiteContent.get("tagline", "Capturing timeless moments with warmth, artistry, and intention."),
        "about":   SiteContent.get("about",   "Founded by a passionate collective of visual storytellers..."),
        "hero_sub": SiteContent.get("hero_sub", "We are Boundless Moments — a team of professional photographers."),
    }
    stats = {
        "years":    SiteContent.get("stat_years",    "8+"),
        "projects": SiteContent.get("stat_projects", "340+"),
        "awards":   SiteContent.get("stat_awards",   "12"),
    }
    return render_template("index.html", featured=featured, content=content, stats=stats)


@app.route("/portfolio")
def portfolio():
    """Portfolio / gallery page — all items, supports ?category= filter."""
    category = request.args.get("category", "all")
    sort     = request.args.get("sort", "newest")

    query = PortfolioItem.query
    if category != "all":
        query = query.filter_by(category=category)
    if sort == "oldest":
        query = query.order_by(PortfolioItem.year.asc())
    elif sort == "az":
        query = query.order_by(PortfolioItem.title.asc())
    else:
        query = query.order_by(PortfolioItem.year.desc())

    items = query.all()
    return render_template(
        "pages/portfolio.html",
        items=items,
        active_category=category,
        active_sort=sort,
        categories=["all", "wedding", "portrait", "landscape", "editorial", "fineart"]
    )


@app.route("/skills")
def skills():
    """Experience & Skills page — team members, skills, timeline, awards."""
    team   = TeamMember.query.order_by(TeamMember.sort_order).all()
    awards = Award.query.order_by(Award.year.desc()).all()
    return render_template("pages/skills.html", team=team, awards=awards)


@app.route("/contact")
def contact():
    """Contact page."""
    content = {
        "email":   SiteContent.get("contact_email",   "hello@boundlessmoments.com"),
        "phone":   SiteContent.get("contact_phone",   "+44 (0) 207 123 4567"),
        "address": SiteContent.get("contact_address", "24 Bermondsey Street, London, SE1 3UJ"),
    }
    return render_template("pages/contact.html", content=content)


# ══════════════════════════════════════════════════════════════════════════════
# CONTACT FORM — POST endpoint
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/contact", methods=["POST"])
def api_contact():
    """Receive contact form submission and store in messages table."""
    data = request.get_json()
    if not data:
        return jsonify({"ok": False, "error": "No data received"}), 400

    required = ["firstName", "lastName", "email", "message"]
    for field in required:
        if not data.get(field, "").strip():
            return jsonify({"ok": False, "error": f"{field} is required"}), 422

    # Parse optional event date
    event_date = None
    if data.get("date"):
        try:
            event_date = date.fromisoformat(data["date"])
        except ValueError:
            pass

    msg = Message(
        first_name = data["firstName"].strip(),
        last_name  = data["lastName"].strip(),
        email      = data["email"].strip().lower(),
        phone      = data.get("phone", "").strip() or None,
        service    = data.get("service", "").strip() or None,
        event_date = event_date,
        message    = data["message"].strip(),
    )
    db.session.add(msg)
    db.session.commit()
    return jsonify({"ok": True, "id": msg.id}), 201


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — AUTH
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        user = AdminUser.query.filter_by(username=data.get("username", "")).first()
        if user and user.check_password(data.get("password", "")):
            login_user(user)
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Invalid credentials"}), 401
    return render_template("pages/admin.html")


@app.route("/admin/logout")
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for("admin_login"))


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/admin")
@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    stats = {
        "portfolio_count": PortfolioItem.query.count(),
        "unread_messages": Message.query.filter_by(is_read=False).count(),
        "total_messages":  Message.query.count(),
        "award_count":     Award.query.count(),
    }
    recent_messages = Message.query.order_by(Message.received_at.desc()).limit(5).all()
    return render_template("pages/admin.html", stats=stats, recent_messages=recent_messages)


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN API — PORTFOLIO
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/admin/portfolio", methods=["GET"])
@login_required
def api_portfolio_list():
    items = PortfolioItem.query.order_by(PortfolioItem.year.desc()).all()
    return jsonify([i.to_dict() for i in items])


@app.route("/api/admin/portfolio", methods=["POST"])
@login_required
def api_portfolio_create():
    data = request.get_json()
    item = PortfolioItem(
        title       = data["title"].strip(),
        category    = data["category"],
        year        = int(data["year"]),
        description = data.get("description", ""),
        featured    = bool(data.get("featured", False)),
        sort_order  = int(data.get("sort_order", 0)),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


@app.route("/api/admin/portfolio/<int:item_id>", methods=["PUT"])
@login_required
def api_portfolio_update(item_id):
    item = PortfolioItem.query.get_or_404(item_id)
    data = request.get_json()
    item.title       = data.get("title", item.title).strip()
    item.category    = data.get("category", item.category)
    item.year        = int(data.get("year", item.year))
    item.description = data.get("description", item.description)
    item.featured    = bool(data.get("featured", item.featured))
    db.session.commit()
    return jsonify(item.to_dict())


@app.route("/api/admin/portfolio/<int:item_id>", methods=["DELETE"])
@login_required
def api_portfolio_delete(item_id):
    item = PortfolioItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"ok": True})


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN API — MESSAGES
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/admin/messages", methods=["GET"])
@login_required
def api_messages_list():
    msgs = Message.query.order_by(Message.received_at.desc()).all()
    return jsonify([m.to_dict() for m in msgs])


@app.route("/api/admin/messages/<int:msg_id>/read", methods=["PATCH"])
@login_required
def api_message_mark_read(msg_id):
    msg = Message.query.get_or_404(msg_id)
    msg.is_read = True
    db.session.commit()
    return jsonify({"ok": True})


@app.route("/api/admin/messages/<int:msg_id>", methods=["DELETE"])
@login_required
def api_message_delete(msg_id):
    msg = Message.query.get_or_404(msg_id)
    db.session.delete(msg)
    db.session.commit()
    return jsonify({"ok": True})


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN API — SITE CONTENT
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/admin/content", methods=["GET"])
@login_required
def api_content_get():
    rows = SiteContent.query.all()
    return jsonify({r.key: r.value for r in rows})


@app.route("/api/admin/content", methods=["POST"])
@login_required
def api_content_update():
    data = request.get_json()
    for key, value in data.items():
        SiteContent.set(key, value)
    db.session.commit()
    return jsonify({"ok": True})




# ══════════════════════════════════════════════════════════════════════════════
# ADMIN API — IMAGE UPLOADS
# POST /api/admin/portfolio/<id>/images   — upload one or more images
# GET  /api/admin/portfolio/<id>/images   — list images for a portfolio item
# DELETE /api/admin/images/<image_id>     — delete a single image
# PATCH  /api/admin/images/<image_id>     — update alt text / sort order
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/admin/portfolio/<int:item_id>/images", methods=["GET"])
@login_required
def api_images_list(item_id):
    """Return all images for a given portfolio item."""
    item = PortfolioItem.query.get_or_404(item_id)
    return jsonify([img.to_dict() for img in item.images])


@app.route("/api/admin/portfolio/<int:item_id>/images", methods=["POST"])
@login_required
def api_images_upload(item_id):
    """Upload one or more image files and attach them to a portfolio item."""
    item = PortfolioItem.query.get_or_404(item_id)

    if "files" not in request.files:
        return jsonify({"ok": False, "error": "No files provided"}), 400

    files   = request.files.getlist("files")
    results = []

    # Ensure upload directory exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    for f in files:
        if not f or not f.filename:
            continue
        if not allowed_file(f.filename):
            return jsonify({"ok": False, "error": f"{f.filename} is not an allowed file type (jpg, png, webp, gif)"}), 422

        # Build a safe, unique filename: uuid_originalname.ext
        ext      = f.filename.rsplit(".", 1)[1].lower()
        safe_name = f"{uuid.uuid4().hex}_{secure_filename(f.filename)}"
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)
        f.save(save_path)

        # Get current max sort order for this item
        max_order = db.session.query(
            db.func.max(GalleryImage.sort_order)
        ).filter_by(portfolio_item_id=item_id).scalar() or 0

        image = GalleryImage(
            portfolio_item_id = item_id,
            filename          = safe_name,
            alt_text          = request.form.get("alt_text", item.title),
            sort_order        = max_order + 1,
        )
        db.session.add(image)
        db.session.flush()   # get ID before commit
        results.append(image.to_dict())

    db.session.commit()
    return jsonify({"ok": True, "uploaded": len(results), "images": results}), 201


@app.route("/api/admin/images/<int:image_id>", methods=["DELETE"])
@login_required
def api_image_delete(image_id):
    """Delete an image record and its file from disk."""
    image = GalleryImage.query.get_or_404(image_id)

    # Remove the file from static/images/
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], image.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(image)
    db.session.commit()
    return jsonify({"ok": True})


@app.route("/api/admin/images/<int:image_id>", methods=["PATCH"])
@login_required
def api_image_update(image_id):
    """Update alt text or sort order of an image."""
    image = GalleryImage.query.get_or_404(image_id)
    data  = request.get_json()
    if "alt_text"   in data: image.alt_text   = data["alt_text"]
    if "sort_order" in data: image.sort_order = int(data["sort_order"])
    db.session.commit()
    return jsonify(image.to_dict())

# ══════════════════════════════════════════════════════════════════════════════
# DB INIT + SEED
# Run once: flask init-db
# ══════════════════════════════════════════════════════════════════════════════

@app.cli.command("init-db")
def init_db():
    """Create all tables and seed initial data."""
    db.create_all()
    print("✓ Tables created.")

    # Seed admin user
    if not AdminUser.query.filter_by(username=os.getenv("ADMIN_USERNAME", "admin")).first():
        admin = AdminUser(username=os.getenv("ADMIN_USERNAME", "admin"))
        admin.set_password(os.getenv("ADMIN_PASSWORD", "boundless2026"))
        db.session.add(admin)
        print("✓ Admin user seeded.")

    # Seed portfolio items
    if not PortfolioItem.query.first():
        seed_portfolio = [
            PortfolioItem(title="The Harlow Wedding",       category="wedding",   year=2025, featured=True,  sort_order=1),
            PortfolioItem(title="Misty Highlands Series",   category="landscape", year=2024, featured=True,  sort_order=2),
            PortfolioItem(title="Clara — Natural Light",    category="portrait",  year=2025, featured=True,  sort_order=3),
            PortfolioItem(title="Urban Grain",              category="editorial", year=2024, featured=False, sort_order=4),
            PortfolioItem(title="Forest Light Study",       category="fineart",   year=2025, featured=True,  sort_order=5),
            PortfolioItem(title="Ashton & Grace",           category="wedding",   year=2024, featured=False, sort_order=6),
            PortfolioItem(title="The Chen Family",          category="portrait",  year=2024, featured=False, sort_order=7),
            PortfolioItem(title="Coastal Dawn Series",      category="landscape", year=2025, featured=True,  sort_order=8),
            PortfolioItem(title="Autumn Couture",           category="editorial", year=2025, featured=False, sort_order=9),
            PortfolioItem(title="Moody Interior Study",     category="fineart",   year=2024, featured=False, sort_order=10),
            PortfolioItem(title="Valley Mist",              category="landscape", year=2025, featured=False, sort_order=11),
            PortfolioItem(title="Elara — Studio Session",   category="portrait",  year=2023, featured=False, sort_order=12),
        ]
        db.session.add_all(seed_portfolio)
        db.session.flush()  # get IDs
        # Map filename to portfolio item by title
        gallery_map = {
            "The Harlow Wedding":       "portfolio_harlow_wedding_1.jpg",
            "Misty Highlands Series":   "portfolio_misty_highlands_1.jpg",
            "Clara — Natural Light":    "portfolio_clara_portrait_1.jpg",
            "Urban Grain":              "portfolio_urban_grain_1.jpg",
            "Forest Light Study":       "portfolio_forest_light_1.jpg",
            "Ashton & Grace":           "portfolio_ashton_grace_1.jpg",
            "The Chen Family":          "portfolio_chen_family_1.jpg",
            "Coastal Dawn Series":      "portfolio_coastal_dawn_1.jpg",
            "Autumn Couture":           "portfolio_autumn_couture_1.jpg",
            "Moody Interior Study":     "portfolio_moody_interior_1.jpg",
            "Valley Mist":              "portfolio_valley_mist_1.jpg",
            "Elara — Studio Session":   "portfolio_elara_studio_1.jpg",
        }
        seed_gallery = []
        for item in seed_portfolio:
            fname = gallery_map.get(item.title)
            if fname:
                seed_gallery.append(GalleryImage(
                    portfolio_item_id=item.id,
                    filename=fname,
                    alt_text=item.title,
                    sort_order=1
                ))
        db.session.add_all(seed_gallery)
        print(f"✓ {len(seed_portfolio)} portfolio items seeded.")
        print(f"✓ {len(seed_gallery)} gallery images seeded.")

    # Seed team members + skills
    if not TeamMember.query.first():
        elena = TeamMember(name="Elena Marchetti", role="Founder · Wedding & Portrait", sort_order=1, photo="team_elena.jpg",
            bio="Elena's sensitivity to light and emotion has defined Boundless Moments' signature style. With 10+ years in wedding and portrait photography, her work has appeared in Vogue Italia and The Telegraph.")
        james = TeamMember(name="James Okafor", role="Lead · Landscape & Documentary", sort_order=2, photo="team_james.jpg",
            bio="James brings an explorer's spirit to every assignment. His landscape series have been exhibited in galleries across London and Edinburgh.")
        priya = TeamMember(name="Priya Sharma", role="Specialist · Editorial & Commercial", sort_order=3, photo="team_priya.jpg",
            bio="With a background in fashion and a degree in Visual Arts, Priya merges aesthetic precision with commercial sensibility.")
        db.session.add_all([elena, james, priya])
        db.session.flush()  # get IDs before adding skills

        skills_data = [
            Skill(team_member_id=elena.id, name="Wedding Photography",  level=96, sort_order=1),
            Skill(team_member_id=elena.id, name="Natural Light Portraits", level=98, sort_order=2),
            Skill(team_member_id=elena.id, name="Adobe Lightroom",      level=92, sort_order=3),
            Skill(team_member_id=james.id, name="Landscape Photography", level=99, sort_order=1),
            Skill(team_member_id=james.id, name="Documentary",           level=90, sort_order=2),
            Skill(team_member_id=james.id, name="Adobe Photoshop",       level=88, sort_order=3),
            Skill(team_member_id=priya.id, name="Editorial Photography", level=94, sort_order=1),
            Skill(team_member_id=priya.id, name="Studio Lighting",       level=91, sort_order=2),
            Skill(team_member_id=priya.id, name="Art Direction",         level=85, sort_order=3),
        ]
        db.session.add_all(skills_data)
        print("✓ Team members and skills seeded.")

    # Seed awards
    if not Award.query.first():
        seed_awards = [
            Award(title="BIPP Qualification Award",     organisation="British Institute of Professional Photography", year=2024, icon="🏆", description="Wedding Photography Excellence"),
            Award(title="International Photography Awards", organisation="IPA New York",           year=2023, icon="🥇", description="Gold Award — Nature & Landscape Category"),
            Award(title="WPJA Award",                   organisation="Wedding Photojournalism Association", year=2022, icon="📸", description="Top 10 UK Photographers"),
            Award(title="Master Photographer",          organisation="SWPP",                       year=2021, icon="🎖", description="Society of Wedding & Portrait Photographers"),
            Award(title="Vogue Italia Feature",         organisation="Condé Nast",                 year=2023, icon="🌟", description="Editorial feature, Couture Photography supplement"),
            Award(title="BBC Documentary",              organisation="BBC Four",                   year=2020, icon="📰", description="Featured in 'The Photographers' documentary series"),
            Award(title="Gallery Noir Exhibition",      organisation="Gallery Noir, Edinburgh",    year=2019, icon="🎨", description="Solo landscape exhibition — 'Between Tides'"),
            Award(title="Fearless Photographer",        organisation="Fearless Photographers",     year=2018, icon="✨", description="Annual wedding photography recognition"),
        ]
        db.session.add_all(seed_awards)
        print(f"✓ {len(seed_awards)} awards seeded.")

    # Seed site content
    if not SiteContent.query.first():
        defaults = {
            "tagline":         "Capturing timeless moments with warmth, artistry, and intention.",
            "hero_sub":        "We are Boundless Moments — a team of professional photographers dedicated to capturing the essence of life's most meaningful scenes.",
            "about":           "Founded by a passionate collective of visual storytellers, Boundless Moments has spent years honing the craft of authentic photography.",
            "stat_years":      "8+",
            "stat_projects":   "340+",
            "stat_awards":     "12",
            "contact_email":   "hello@boundlessmoments.com",
            "contact_phone":   "+44 (0) 207 123 4567",
            "contact_address": "24 Bermondsey Street, London, SE1 3UJ",
        }
        for key, value in defaults.items():
            SiteContent.set(key, value)
        print("✓ Site content seeded.")

    db.session.commit()
    print("\n✅ Database initialised successfully.")
    print("   Run: flask run")


if __name__ == "__main__":
    app.run(debug=True)
