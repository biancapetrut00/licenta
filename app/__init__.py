from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()



def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'get me out'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    from .models import User
    from .models import Category
    from .models import Forum

    with app.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = 'authentication.login'
    login_manager.init_app(app)


    from .views import views
    from .authentication import authentication

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(authentication, url_prefix='/')



    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app
