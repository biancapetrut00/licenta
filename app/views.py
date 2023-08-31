from flask import render_template, Blueprint, request, flash, redirect, url_for, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from . import db
from .models import Category, Forum, User, Comments
from datetime import datetime
import pytz

#from app.models import User, Post


views = Blueprint('views', __name__)

@views.route('/')
def index():

    return render_template("index.html", user=current_user)

@views.route('/forum')
def forum():

    return render_template("forum.html", user=current_user)



@views.route('/forum/<subject>')
def get_categories_by_subject(subject):
    categories = Category.query.filter_by(subject=subject).all()
    category_list = [{'id': category.id, 'name': category.categoryName} for category in categories]
    return jsonify(category_list)


@views.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        if current_user.isAdmin:  # Only admins can submit this form
            category_name = request.form.get('categoryName')
            subject = request.form.get('subject')

            # Check if category already exists
            old_category = Category.query.filter_by(categoryName=category_name).first()
            if old_category:
                flash("The category you are trying to add already exists", 'error')
            elif len(category_name)<1:
                flash("Category name field cannot be empty", 'error')
            else:
                # Create a new Category object and add it to the database
                new_category = Category(categoryName=category_name, subject=subject)
                db.session.add(new_category)
                db.session.commit()

                flash('Category added successfully!', 'success')

                return redirect(url_for('views.profile'))  # Redirect to the profile page

    return render_template('profile.html', user=current_user)





@views.route('/create_post', methods=['GET', 'POST'])
def create_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        subject_id = request.form.get('subject')  # Get subject ID from the form
        category_id = request.form.get('category')  # Get category ID from the form


        if len(title)<1:
            flash('Please fill in the title')
        if len(content)<1:
            flash('Please fill in the content')

        if current_user.is_authenticated:
            user_id = current_user.id
        else:
            user_id = 0;

        current_time_utc = datetime.now(pytz.utc)

        # Set your desired timezone (replace 'Your/Timezone' with the actual timezone identifier)
        your_timezone = pytz.timezone('Europe/Bucharest')

        # Convert the UTC time to your timezone
        current_time = current_time_utc.astimezone(your_timezone)

        # Create and add the new post to the database
        new_post = Forum(title=title, content=content, user_id=user_id, category_id=category_id, date_added=current_time)
        db.session.add(new_post)
        db.session.commit()

        flash('Post created successfully!', 'success')
        return redirect(url_for('views.index'))

    # Fetch the categories for populating the dropdown
    categories = Category.query.all()

    return render_template('create_post.html', categories=categories, user=current_user)



@views.route('/forum/all_posts', methods=['GET'])
def get_all_posts():
    all_posts = Forum.query.all()
    posts_data = []

    for post in all_posts:
        category = Category.query.get(post.category_id)  # Get the category related to the post
        user = User.query.get(post.user_id)  # Get the user related to the post
        post_data = {
            "id" :post.id,
            "title": post.title,
            "content": post.content,
            "subject": category.subject if category else "Unknown",
            "category": category.categoryName if category else "Unknown",
            "author": user.username if user else "Unknown",
            "date_added": post.date_added
        }
        posts_data.append(post_data)

    return jsonify(posts_data)


@views.route('/forum/category/<category_name>', methods=['GET'])
def get_posts_by_category(category_name):
    category = Category.query.filter_by(categoryName=category_name).first()
    if not category:
        return jsonify([])  # Return an empty list if category doesn't exist

    posts = Forum.query.filter_by(category_id=category.id).all()
    posts_data = []

    for post in posts:
        user = User.query.get(post.user_id)  # Get the user related to the post
        post_data = {
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "subject": category.subject,
            "category": category.categoryName,
            "author": user.username if user else "Unknown",  # Use the username or "Unknown" if user not found
            "date_added": post.date_added
        }
        posts_data.append(post_data)

    return jsonify(posts_data)

@views.route('/forum/post/<int:post_id>', methods=['GET', 'POST'])
def get_post_by_id(post_id):
    post = Forum.query.get(post_id)
    if not post:
        return "Post not found", 404

    category = Category.query.get(post.category_id)
    user = User.query.get(post.user_id)

    post_data = {
        "title": post.title,
        "content": post.content,
        "subject": category.subject if category else "Unknown",
        "category": category.categoryName if category else "Unknown",
        "author": user.username if user else "Unknown",
        "date_added": post.date_added
    }

    if request.method == 'POST':
        comment_text = request.form.get('comment')

        if current_user.is_authenticated:
            user_id = current_user.id
        else:
            user_id = 0

        current_time_utc = datetime.now(pytz.utc)
        your_timezone = pytz.timezone('Europe/Bucharest')
        current_time = current_time_utc.astimezone(your_timezone)

        new_comment = Comments(content=comment_text, user_id=user_id, post_id=post_id, date_added=current_time)
        db.session.add(new_comment)
        db.session.commit()

        flash('Comment added successfully!', 'success')

        # Redirect to the same page to avoid form resubmission
        return redirect(url_for('views.get_post_by_id', post_id=post_id))
    # Fetch comments for the post
    comments = Comments.query.filter_by(post_id=post_id).all()

    return render_template('post.html', post=post_data, comments=comments, user=current_user)








