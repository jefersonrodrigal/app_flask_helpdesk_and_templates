from flask import Flask, request, render_template, session as usersession, redirect
from sqlalchemy.orm import Session
from models import engine, Base, User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user
from datetime import datetime
import secrets

app = Flask(__name__)
Base.metadata.create_all(engine)
login_manager = LoginManager()
login_manager.init_app(app)
app.secret_key = secrets.token_hex()


@login_manager.user_loader
def load_user(user_id):
    with Session(engine) as session:
        user: User = session.query(User).filter(User.id == user_id).scalar()
    return user


@app.route('/cadastrousuarios', methods=['GET', 'POST'])
def insert_user():
    if request.method == 'POST':
        name: str = request.form.get('name')
        lastname: str = request.form.get('lastnbame')
        email: str = request.form.get('email')
        password: str = request.form.get('password')

        hashed: str = generate_password_hash(password, method='scrypt')

        with Session(engine) as session:
            user: User = User(name=name, lastname=lastname,
                              email=email, password=hashed)

            session.add(user)
            session.commit()

        return render_template('cadastro.html')

    return render_template('cadastro.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if email != '' and password != '':
            user: User = Session(engine).query(User).filter(
                User.email == email).scalar()
        if user:
            check_pwd = check_password_hash(user.password, password)

            if check_pwd:
                usersession['id'] = user.id
                usersession['token'] = secrets.token_hex()

                login_user(user)

                with Session(engine) as sesssion:
                    user: User = sesssion.query(User).filter(
                        User.id == usersession.get('id')).scalar()
                    user.token = usersession.get("token")
                    user.last_session = datetime.now()
                    sesssion.add(user)
                    sesssion.commit()

                return redirect(f'/usuarioinicio/{usersession.get("id")}/{usersession.get("token")}')

    return render_template('login.html')


@app.route('/usuarioinicio/<id>/<token>')
@login_required
def user_profile(id, token):
    user_id: User = Session(engine).query(User).filter(
        User.id == id, User.token == token).scalar()

    if not user_id:
        return login_manager.unauthorized()

    return 'My Profile'


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)
