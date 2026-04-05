from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    course = db.Column(db.Integer, nullable=False)
    faculty = db.Column(db.String(200), nullable=False)
    students = db.relationship('User', backref='group', lazy=True)
    lessons = db.relationship('Lesson', backref='group', lazy=True, cascade='all, delete-orphan')


class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    lessons = db.relationship('Lesson', backref='subject', lazy=True, cascade='all, delete-orphan')


class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    department = db.Column(db.String(200))
    lessons = db.relationship('Lesson', backref='teacher', lazy=True, cascade='all, delete-orphan')


class Room(db.Model):
    __tablename__ = 'rooms'
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(20), nullable=False)
    building = db.Column(db.String(100))
    capacity = db.Column(db.Integer, default=30)
    room_type = db.Column(db.String(50), default='Лекционная')
    lessons = db.relationship('Lesson', backref='room', lazy=True, cascade='all, delete-orphan')


class Lesson(db.Model):
    __tablename__ = 'lessons'
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)
    time_slot = db.Column(db.Integer, nullable=False)
    lesson_type = db.Column(db.String(20), nullable=False, default='Лекция')
    week_type = db.Column(db.String(20), default='Каждая')
