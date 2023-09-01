from flask import render_template, request, redirect, url_for, Blueprint, flash, abort
from flask_login import current_user, login_required, login_manager
from app import db
from app.models import Quiz, Question, Option
from functools import wraps
import re

quiz = Blueprint('quiz', __name__)


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.isAdmin:
            abort(403)  # Forbidden
        return func(*args, **kwargs)
    return wrapper


@quiz.route('/create_quiz', methods=['GET', 'POST'])
@admin_required
def create_quiz():
    if request.method == 'POST':
        quiz_title = request.form.get('quiz_title')
        quiz = Quiz(title=quiz_title)
        db.session.add(quiz)
        db.session.commit()

        question_index = 0
        while f'question[{question_index}][text]' in request.form:
            question_text = request.form.get(f'question[{question_index}][text]')
            question = Question(text=question_text, quiz=quiz)
            db.session.add(question)
            db.session.commit()

            option_index = 0
            while f'question[{question_index}][options][{option_index}][option]' in request.form:
                option_text = request.form.get(f'question[{question_index}][options][{option_index}][option]')
                is_correct = request.form.get(f'question[{question_index}][options][{option_index}][is_correct]', False)

                # Convert 'on' to True and None to False
                if is_correct == 'on':
                    is_correct = True
                else:
                    is_correct = False

                option = Option(text=option_text, is_correct=is_correct, question=question)
                db.session.add(option)
                db.session.commit()

                option_index += 1

            question_index += 1

        return redirect(url_for('quiz.create_quiz'))

    return render_template('create_quiz.html', user=current_user)


@quiz.route('/quiz/<int:quiz_id>', methods=['GET', 'POST'])
def take_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return "Quiz not found", 404

    if request.method == 'POST':
        total_questions = len(quiz.questions)
        user_score = 0

        for question in quiz.questions:
            selected_option_id = int(request.form.get(f'question{question.id}', -1))
            correct_option_id = next((option.id for option in question.options if option.is_correct), None)

            if selected_option_id == correct_option_id:
                user_score += 1

        flash(f'Your score: {user_score}/{total_questions}', 'quiz_result')
        return redirect(url_for('quiz.take_quiz', quiz_id=quiz_id))

    return render_template('quiz.html', quiz=quiz, user=current_user)

@quiz.route('/quizzes', methods=['GET'])
def quizzes():
    is_teacher = False  # Initialize the variable

    if current_user.is_authenticated:
        is_teacher = current_user.isAdmin  # Check if the user is a teacher (isAdmin)
    quizzes = Quiz.query.all()
    return render_template('quizzes.html', quizzes=quizzes, user=current_user, is_teacher=is_teacher)

