from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from models import db, Usuario
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///projetost.db"

db.init_app(app)

with app.app_context():
    db.create_all()
    

@app.route("/")
@app.route("/index")
@app.route("/home")
def home():
    return render_template("index.html")

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():

    if request.method == "POST":
        nome=request.form.get("nome", "").strip()
        sobrenome=request.form.get("sobrenome", "").strip()
        email=request.form.get("email", "").strip().lower()
        senha=request.form.get("senha", "")

        if not nome or not sobrenome or not email or len(senha)<8:
            flash("Preencha todos os campos corretamente", "erro")
            return redirect(url_for("cadastro"))

        usuario_existe = db.session.execute(
            db.select(Usuario).filter_by(email=email)
        ).scalar_one_or_none()

        if usuario_existe:
            flash("Esse e-mail já está cadastrado, tente novamente", "erro")
            return redirect(url_for("cadastro"))

        senha_hash = generate_password_hash(senha)

        novo_usuario = Usuario(
            nome=nome,
            sobrenome=sobrenome,
            email=email,
            senha_hash=senha_hash
        )

        try:
            db.session.add(novo_usuario)
            db.session.commit()

        except IntegrityError:
            db.session.rollback()
            flash("Não foi possível completar o cadastro", "erro")
            return redirect(url_for("cadastro"))

        flash("Cadastro realizado com sucesso!", "sucesso")
        return redirect(url_for("login"))

    return render_template("cadastro.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        senha = request.form.get("senha","")

        usuario = db.session.execute(
            db.select(Usuario).filter_by(email=email)
        ).scalar_one_or_none()

        if usuario and check_password_hash(usuario.senha_hash, senha):
            session.clear()

            session["usuario_id"] = usuario.id
            session["usuario_nome"] = usuario.nome
            session["is_admin"] = usuario.email == "admin@admin.projetost"

            flash("Login realizado com sucesso!", "sucesso")
            return redirect(url_for("home"))

        flash ("E-mail ou senha incorretos", "erro")
        return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout", methods=["POST", "GET"])
def logout():
    session.clear()
    flash("Você saiu da sua conta.", "sucesso")
    return redirect(url_for("home"))

@app.route("/catalogo")
def catalogo():
    if session.get("usuario_id"):
        return render_template("catalogo_precos.html")

    return render_template("catalogo_sem_precos.html")

if __name__=="__main__":
    app.run(debug=True)