from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

db = SQLAlchemy()

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False)
    last_updated = db.Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f'<Category {self.name}>'


class Set(db.Model):
    __tablename__ = 'sets'
    id = db.Column(Integer, primary_key=True)
    set_number = db.Column(String, nullable=False)
    name = db.Column(String, nullable=True)
    set_img_url = db.Column(String, nullable=True)

    # Relationships
    user_sets = db.relationship("UserSet", back_populates="template_set", cascade="all, delete-orphan", lazy=True)

    def __repr__(self):
        return f'<Set {self.set_number} - {self.name} (ID: {self.id})>'


class UserSet(db.Model):
    __tablename__ = 'user_sets'
    id = db.Column(Integer, primary_key=True)
    set_id = db.Column(Integer, ForeignKey('sets.id'), nullable=False)
    status = db.Column(String, default='unknown', nullable=False)

    # Relationships
    template_set = db.relationship('Set', back_populates='user_sets')
    parts = db.relationship("Part", back_populates="user_set", cascade="all, delete-orphan", lazy=True)
    minifigures = db.relationship("Minifigure", back_populates="user_set", cascade="all, delete-orphan", lazy=True)
    minifigure_parts = db.relationship("UserMinifigurePart", back_populates="user_set", cascade="all, delete-orphan", lazy=True)

    def __repr__(self):
        return f'<UserSet {self.id} for Set {self.set_id}>'


class Part(db.Model):
    __tablename__ = 'parts'
    id = db.Column(Integer, primary_key=True)
    part_num = db.Column(String, nullable=False)
    name = db.Column(String, nullable=False)
    category_id = db.Column(Integer, db.ForeignKey('categories.id'), nullable=True)
    color = db.Column(String, nullable=False)
    color_rgb = db.Column(String, nullable=True)
    quantity = db.Column(Integer, nullable=False)
    have_quantity = db.Column(Integer, default=0)
    part_img_url = db.Column(String, nullable=True)
    part_url = db.Column(String, nullable=True)
    user_set_id = db.Column(Integer, ForeignKey('user_sets.id'), nullable=False)
    is_spare = db.Column(db.Boolean, default=False, nullable=False)

    # Relationships
    user_set = db.relationship("UserSet", back_populates="parts")
    category = db.relationship('Category', backref='parts', lazy='joined')  # Proper relationship

    def __repr__(self):
        return f'<Part {self.part_num} - {self.name}>'



class Minifigure(db.Model):
    __tablename__ = 'minifigures'
    id = db.Column(Integer, primary_key=True)
    fig_num = db.Column(String, nullable=False)
    name = db.Column(String, nullable=False)
    quantity = db.Column(Integer, nullable=False)
    have_quantity = db.Column(Integer, default=0)
    img_url = db.Column(String, nullable=True)
    user_set_id = db.Column(Integer, ForeignKey('user_sets.id'), nullable=False)

    # Relationships
    user_set = db.relationship("UserSet", back_populates="minifigures")
    parts = db.relationship("MinifigurePart", back_populates="minifigure", cascade="all, delete-orphan", lazy=True)

    def __repr__(self):
        return f'<Minifigure {self.fig_num} - {self.name}>'


class MinifigurePart(db.Model):
    __tablename__ = 'minifigure_parts'
    id = db.Column(Integer, primary_key=True)
    part_num = db.Column(String, nullable=False)
    name = db.Column(String, nullable=False)
    color = db.Column(String, nullable=True)
    color_rgb = db.Column(String, nullable=True)
    quantity = db.Column(Integer, nullable=False)
    part_img_url = db.Column(String, nullable=True)
    part_url = db.Column(String, nullable=True)
    minifigure_id = db.Column(Integer, ForeignKey('minifigures.id'), nullable=False)
    is_spare = db.Column(db.Boolean, default=False, nullable=False)

    # Relationships
    minifigure = db.relationship("Minifigure", back_populates="parts")

    def __repr__(self):
        return f'<MinifigurePart {self.part_num} - {self.name}>'


class UserMinifigurePart(db.Model):
    __tablename__ = 'user_minifigure_parts'
    id = db.Column(Integer, primary_key=True)
    part_num = db.Column(String, nullable=False)
    name = db.Column(String, nullable=False)
    color = db.Column(String, nullable=True)
    color_rgb = db.Column(String, nullable=True)
    quantity = db.Column(Integer, nullable=False)
    have_quantity = db.Column(Integer, default=0)  # Track ownership
    part_img_url = db.Column(String, nullable=True)
    part_url = db.Column(String, nullable=True)
    user_set_id = db.Column(Integer, ForeignKey('user_sets.id'), nullable=False)
    is_spare = db.Column(db.Boolean, default=False, nullable=False)

    # Relationships
    user_set = db.relationship("UserSet", back_populates="minifigure_parts")

    def __repr__(self):
        return f'<UserMinifigurePart {self.part_num} - {self.name}>'
