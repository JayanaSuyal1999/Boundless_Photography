from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


# ─────────────────────────────────────────────────────────────────────────────
# TABLE: admin_users
# Stores admin login credentials. Uses hashed passwords — never plain text.
# ─────────────────────────────────────────────────────────────────────────────
class AdminUser(UserMixin, db.Model):
    __tablename__ = "admin_users"

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<AdminUser {self.username}>"


# ─────────────────────────────────────────────────────────────────────────────
# TABLE: portfolio_items
# Each row is one portfolio project (wedding, portrait, etc.)
# One portfolio_item can have many gallery_images (one-to-many).
# ─────────────────────────────────────────────────────────────────────────────
class PortfolioItem(db.Model):
    __tablename__ = "portfolio_items"

    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    category    = db.Column(db.String(80), nullable=False)   # wedding|portrait|landscape|editorial|fineart
    year        = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=True)
    featured    = db.Column(db.Boolean, default=False)       # show on homepage
    sort_order  = db.Column(db.Integer, default=0)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship: one portfolio item → many gallery images
    images = db.relationship(
        "GalleryImage",
        back_populates="portfolio_item",
        cascade="all, delete-orphan",
        order_by="GalleryImage.sort_order"
    )

    def to_dict(self):
        return {
            "id":          self.id,
            "title":       self.title,
            "category":    self.category,
            "year":        self.year,
            "description": self.description,
            "featured":    self.featured,
            "sort_order":  self.sort_order,
            "created_at":  self.created_at.isoformat(),
            "image_count": len(self.images),
            "cover_image": self.images[0].to_dict() if self.images else None,
        }

    def __repr__(self):
        return f"<PortfolioItem {self.title} ({self.year})>"


# ─────────────────────────────────────────────────────────────────────────────
# TABLE: gallery_images
# Individual images that belong to a portfolio item.
# Foreign key → portfolio_items.id
# ─────────────────────────────────────────────────────────────────────────────
class GalleryImage(db.Model):
    __tablename__ = "gallery_images"

    id                 = db.Column(db.Integer, primary_key=True)
    portfolio_item_id  = db.Column(
        db.Integer,
        db.ForeignKey("portfolio_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    filename           = db.Column(db.String(255), nullable=False)  # stored in static/images/
    alt_text           = db.Column(db.String(300), nullable=True)
    sort_order         = db.Column(db.Integer, default=0)
    uploaded_at        = db.Column(db.DateTime, default=datetime.utcnow)

    # Back-reference to parent portfolio item
    portfolio_item = db.relationship("PortfolioItem", back_populates="images")

    def to_dict(self):
        return {
            "id":                self.id,
            "portfolio_item_id": self.portfolio_item_id,
            "filename":          self.filename,
            "url":               f"/static/images/{self.filename}",
            "alt_text":          self.alt_text,
            "sort_order":        self.sort_order,
        }

    def __repr__(self):
        return f"<GalleryImage {self.filename}>"


# ─────────────────────────────────────────────────────────────────────────────
# TABLE: team_members
# Photographer profiles shown on the Experience & Skills page.
# One team_member has many skills (one-to-many).
# ─────────────────────────────────────────────────────────────────────────────
class TeamMember(db.Model):
    __tablename__ = "team_members"

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(150), nullable=False)
    role        = db.Column(db.String(150), nullable=False)
    bio         = db.Column(db.Text, nullable=True)
    photo       = db.Column(db.String(255), nullable=True)  # filename in static/images/
    instagram   = db.Column(db.String(200), nullable=True)
    fivehundred = db.Column(db.String(200), nullable=True)  # 500px URL
    sort_order  = db.Column(db.Integer, default=0)

    # Relationship: one member → many skills
    skills = db.relationship(
        "Skill",
        back_populates="team_member",
        cascade="all, delete-orphan",
        order_by="Skill.sort_order"
    )

    def to_dict(self):
        return {
            "id":           self.id,
            "name":         self.name,
            "role":         self.role,
            "bio":          self.bio,
            "photo":        self.photo,
            "instagram":    self.instagram,
            "fivehundred":  self.fivehundred,
            "skills":       [s.to_dict() for s in self.skills],
        }

    def __repr__(self):
        return f"<TeamMember {self.name}>"


# ─────────────────────────────────────────────────────────────────────────────
# TABLE: skills
# Individual skill bars for each team member.
# Foreign key → team_members.id
# ─────────────────────────────────────────────────────────────────────────────
class Skill(db.Model):
    __tablename__ = "skills"

    id             = db.Column(db.Integer, primary_key=True)
    team_member_id = db.Column(
        db.Integer,
        db.ForeignKey("team_members.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name           = db.Column(db.String(150), nullable=False)
    level          = db.Column(db.Integer, nullable=False)   # 0–100 (percentage)
    sort_order     = db.Column(db.Integer, default=0)

    team_member = db.relationship("TeamMember", back_populates="skills")

    def to_dict(self):
        return {
            "id":             self.id,
            "team_member_id": self.team_member_id,
            "name":           self.name,
            "level":          self.level,
        }

    def __repr__(self):
        return f"<Skill {self.name} {self.level}%>"


# ─────────────────────────────────────────────────────────────────────────────
# TABLE: awards
# Awards & recognitions shown on the Experience page.
# ─────────────────────────────────────────────────────────────────────────────
class Award(db.Model):
    __tablename__ = "awards"

    id           = db.Column(db.Integer, primary_key=True)
    title        = db.Column(db.String(200), nullable=False)
    organisation = db.Column(db.String(200), nullable=True)
    description  = db.Column(db.Text, nullable=True)
    year         = db.Column(db.Integer, nullable=False)
    icon         = db.Column(db.String(10), default="🏆")   # emoji icon
    sort_order   = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            "id":           self.id,
            "title":        self.title,
            "organisation": self.organisation,
            "description":  self.description,
            "year":         self.year,
            "icon":         self.icon,
        }

    def __repr__(self):
        return f"<Award {self.title} ({self.year})>"


# ─────────────────────────────────────────────────────────────────────────────
# TABLE: messages
# Contact form submissions from visitors.
# ─────────────────────────────────────────────────────────────────────────────
class Message(db.Model):
    __tablename__ = "messages"

    id          = db.Column(db.Integer, primary_key=True)
    first_name  = db.Column(db.String(100), nullable=False)
    last_name   = db.Column(db.String(100), nullable=False)
    email       = db.Column(db.String(200), nullable=False)
    phone       = db.Column(db.String(50), nullable=True)
    service     = db.Column(db.String(100), nullable=True)  # wedding|portrait|etc
    event_date  = db.Column(db.Date, nullable=True)
    message     = db.Column(db.Text, nullable=False)
    is_read     = db.Column(db.Boolean, default=False, index=True)
    received_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def to_dict(self):
        return {
            "id":          self.id,
            "name":        self.full_name,
            "first_name":  self.first_name,
            "last_name":   self.last_name,
            "email":       self.email,
            "phone":       self.phone,
            "service":     self.service,
            "event_date":  self.event_date.isoformat() if self.event_date else None,
            "message":     self.message,
            "is_read":     self.is_read,
            "received_at": self.received_at.strftime("%d %b %Y, %H:%M"),
        }

    def __repr__(self):
        return f"<Message from {self.full_name} ({self.email})>"


# ─────────────────────────────────────────────────────────────────────────────
# TABLE: site_content
# Key–value store for editable website copy (tagline, about text, etc.)
# Admin can update these from the admin panel without touching HTML.
# ─────────────────────────────────────────────────────────────────────────────
class SiteContent(db.Model):
    __tablename__ = "site_content"

    id         = db.Column(db.Integer, primary_key=True)
    key        = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value      = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get(cls, key, default=""):
        """Convenience method: SiteContent.get('tagline')"""
        row = cls.query.filter_by(key=key).first()
        return row.value if row else default

    @classmethod
    def set(cls, key, value):
        """Upsert a content value."""
        row = cls.query.filter_by(key=key).first()
        if row:
            row.value = value
            row.updated_at = datetime.utcnow()
        else:
            row = cls(key=key, value=value)
            db.session.add(row)

    def __repr__(self):
        return f"<SiteContent {self.key}>"
