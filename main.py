from flask import Flask

from app import create_app

if __name__ == '__main__':
    app = Flask("StudyHelp")
    with app.app_context():
        app = create_app()
        app.run(debug=True)