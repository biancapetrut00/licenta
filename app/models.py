from datetime import datetime
from . import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    isAdmin = db.Column(db.Boolean, default=False)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    categoryName = db.Column(db.String(50), unique=True, nullable=False)
    subject = db.Column(db.String(20), nullable=False)


class Forum(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50))
    content = db.Column(db.String(512))

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship('Category', backref=db.backref('forums', lazy=True))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('forums', lazy=True))

    date_added = db.Column(db.DateTime, default=datetime.utcnow)


class Comments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(512))

    post_id = db.Column(db.Integer, db.ForeignKey('forum.id'), nullable=False)
    post = db.relationship('Forum', backref=db.backref('comments', lazy=True))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('comments', lazy=True))

    date_added = db.Column(db.DateTime, default=datetime.utcnow)


class Lectures(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50))
    fileName = db.Column(db.String(50))

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship('Category', backref=db.backref('lectures', lazy=True))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('lectures', lazy=True))

    date_added = db.Column(db.DateTime, default=datetime.utcnow)





class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    questions = db.relationship('Question', backref='quiz', lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    options = db.relationship('Option', backref='question', lazy=True)

class Option(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)

