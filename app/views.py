import os
from functools import wraps

from flask import render_template, Blueprint, request, flash, redirect, url_for, jsonify, send_from_directory, abort
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename

from . import db
from .models import Category, Forum, User, Comments, Lectures
from datetime import datetime
import pytz

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.isAdmin:
            abort(403)  # Forbidden
        return func(*args, **kwargs)
    return wrapper


#from app.models import User, Post


views = Blueprint('views', __name__)

@views.route('/')
def index():

    return render_template("index.html", user=current_user)


@views.route('/app/static/files/<filename>')
def serve_pdf(filename):
    return send_from_directory('static/files', filename)

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
        if 'categoryName' in request.form:
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


        elif 'newUsername' in request.form:
            newUsername = request.form.get('newUsername')
            old_user = User.query.filter_by(username=newUsername).first()
            if len(newUsername) < 3:
                flash('Username should have at least 3 characters', 'error')
            elif len(newUsername) > 30:
                flash('Username should not exceed 30 characters', 'error')
            elif old_user:
                flash("Username already exists", 'error')
            else:
                current_user.username = newUsername
                db.session.commit()  # Save changes to the database
                flash('Username changed successfully!', 'success')

        elif 'newEmail' in request.form:
            newEmail = request.form.get('newEmail')
            old_email = User.query.filter_by(email=newEmail).first()
            if old_email:
                flash('Email is already in use', 'error')
            else:
                current_user.email = newEmail
                db.session.commit()  # Save changes to the database
                flash('Email changed successfully!', 'success')

        elif 'currentPassword' in request.form:
            currentPassword = request.form.get('currentPassword')
            newPassword = request.form.get('newPassword')
            confirmPassword = request.form.get('confirmPassword')

            if currentPassword != current_user.password:
                flash('Your password is incorrect')
            if newPassword != confirmPassword:
                flash('Passwords don\'t match!', 'error')
            elif len(newPassword) < 6:
                flash('Password should have a minimum of 6 characters', 'error')
            elif len(newPassword) > 30:
                flash('Password cannot exceed 30 characters', 'error')
            else:
                current_user.password = newPassword
                db.session.commit()  # Save changes to the database
                flash('Password changed successfully!', 'success')

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
        return redirect(url_for('views.get_post_by_id', post_id=new_post.id))

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
        if user:
            if user.isAdmin:
                isAdmin = "Teacher"
            else:
                isAdmin = "Student"
        else:
            isAdmin = "Student"
        post_data = {
            "id" :post.id,
            "title": post.title,
            "content": post.content,
            "subject": category.subject if category else "Unknown",
            "category": category.categoryName if category else "Unknown",
            "author": user.username if user else "Guest",
            "isAdmin": isAdmin,
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
        if user:
            if user.isAdmin:
                isAdmin = "Teacher"
            else:
                isAdmin = "Student"
        else:
            isAdmin = "Student"

        post_data = {
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "subject": category.subject,
            "category": category.categoryName,
            "author": user.username if user else "Guest",  # Use the username or "Unknown" if user not found
            "isAdmin": isAdmin,
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
    postUser = User.query.get(post.user_id)
    if postUser:
        if postUser.isAdmin:
            isAdmin = "Teacher"
        else:
            isAdmin = "Student"
    else:
        isAdmin = "Student"
    post_data = {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "subject": category.subject if category else "Unknown",
        "category": category.categoryName if category else "Unknown",
        "author": postUser.username if postUser else "Guest",
        "isAdmin": isAdmin,
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

    comment_data = []
    for comment in comments:
        comment_user = User.query.get(comment.user_id)
        if comment_user:
            if comment_user.isAdmin:
                comment_isAdmin = "Teacher"
            else:
                comment_isAdmin = "Student"
            comment_author = comment_user.username
        else:
            comment_isAdmin = "Student"
            comment_author = "Guest"

        comment_item = {
            "id": comment.id,
            "content": comment.content,
            "author": comment_author,
            "isAdmin": comment_isAdmin,
            "date_added": comment.date_added
        }
        comment_data.append(comment_item)
    postUser = postUser.id if postUser else None

    return render_template('post.html', post=post_data, comments=comment_data, user=current_user, postUser=postUser)


@views.route('/delete_comment/<int:comment_id>', methods=['POST'])
@login_required  # Ensure the user is logged in to perform this action
def delete_comment(comment_id):
    comment = Comments.query.get(comment_id)
    post_id = comment.post_id
    print(current_user.id, comment.user_id)

    if not comment:
        flash("Comment not found", "danger")
        return redirect(url_for('views.get_post_by_id', post_id=post_id))  # Redirect back to the post

    if current_user.id != comment.user_id and not current_user.isAdmin:
        flash("You do not have permission to delete this comment", "danger")
        return redirect(url_for('views.get_post_by_id', post_id=post_id))  # Redirect back to the post

    # Delete the comment
    db.session.delete(comment)
    db.session.commit()

    flash("Comment deleted successfully", "success")
    return redirect(url_for('views.get_post_by_id', post_id=post_id))  # Redirect back to the post


@views.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required  # Ensure the user is logged in to perform this action
def delete_post(post_id):
    post = Forum.query.get(post_id)

    if not post:
        flash("Post not found", "danger")
        return redirect(url_for('views.forum'))  # Redirect to the homepage or another appropriate page

    if current_user.id != post.user_id and not current_user.isAdmin:
        flash("You do not have permission to delete this post", "danger")
        return redirect(url_for('views.get_post_by_id', post_id=post_id))  # Redirect back to the post

    # Delete the post and its associated comments
    Comments.query.filter_by(post_id=post_id).delete()
    db.session.delete(post)
    db.session.commit()

    flash("Post deleted successfully", "success")
    return redirect(url_for('views.forum'))  # Redirect to the homepage or another appropriate page



@views.route('/lectures')
def lectures():
    is_teacher = False  # Initialize the variable

    if current_user.is_authenticated:
        is_teacher = current_user.isAdmin  # Check if the user is a teacher (isAdmin)

    return render_template("lectures.html", user=current_user, is_teacher=is_teacher)

@views.route('/lectures/<subject>')
def get_categories_by_subject_lectures(subject):
    categories = Category.query.filter_by(subject=subject).all()
    category_list = [{'id': category.id, 'name': category.categoryName} for category in categories]
    return jsonify(category_list)



@views.route('/lectures/upload', methods=['GET', 'POST'])
@admin_required
def upload_lecture():
    cwd = os.getcwd()  # Get the current working directory (cwd)
    files = os.listdir(cwd)  # Get all the files in that directory
    print("Files in %r: %s" % (cwd, files))
    if request.method == 'POST':
        title = request.form.get('title')
        subject_id = request.form.get('subject')  # Get subject ID from the form
        category_id = request.form.get('category')  # Get category ID from the form
        file = request.files['pdf_file']

        if current_user.is_authenticated and current_user.isAdmin:

            user_id = current_user.id

            if len(title)<1:
                flash('Please fill in the title')
            if file.filename == '':
                flash('Please upload a file!', category='error')
            else:
                filename = secure_filename(file.filename)
                file.save(os.path.join('app/static/files/', filename))
                Lectures.filename = filename


                current_time_utc = datetime.now(pytz.utc)

                # Set your desired timezone (replace 'Your/Timezone' with the actual timezone identifier)
                your_timezone = pytz.timezone('Europe/Bucharest')

                # Convert the UTC time to your timezone
                current_time = current_time_utc.astimezone(your_timezone)

                # Create and add the new post to the database
                new_lecture = Lectures(title=title, fileName=filename, user_id=user_id, category_id=category_id, date_added=current_time)
                db.session.add(new_lecture)
                db.session.commit()

                flash('Post created successfully!', 'success')
                return redirect(url_for('views.index'))

    # Fetch the categories for populating the dropdown
    categories = Category.query.all()

    return render_template('upload_lecture.html', categories=categories, user=current_user)


@views.route('/lectures/all_lectures', methods=['GET'])
def get_all_lectures():
    all_lectures = Lectures.query.all()
    lectures_data = []

    for lecture in all_lectures:
        category = Category.query.get(lecture.category_id)
        user = User.query.get(lecture.user_id)

        lecture_data = {
            "id": lecture.id,
            "title": lecture.title,
            "subject": category.subject if category else "Unknown",
            "category": category.categoryName if category else "Unknown",
            "author": user.username if user else "Unknown",
            "date_added": lecture.date_added,
            "fileName": lecture.fileName
        }
        lectures_data.append(lecture_data)

    return jsonify(lectures_data)

@views.route('/lectures/category/<category_name>', methods=['GET'])
def get_posts_by_category_lectures(category_name):
    category = Category.query.filter_by(categoryName=category_name).first()
    if not category:
        return jsonify([])

    lectures = Lectures.query.filter_by(category_id=category.id).all()
    lectures_data = []

    for lecture in lectures:
        user = User.query.get(lecture.user_id)

        lecture_data = {
            "id": lecture.id,
            "title": lecture.title,
            "subject": category.subject,
            "category": category.categoryName,
            "author": user.username if user else "Unknown",
            "date_added": lecture.date_added,
            "fileName": lecture.fileName
        }
        lectures_data.append(lecture_data)

    return jsonify(lectures_data)



