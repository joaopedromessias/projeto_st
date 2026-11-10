from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from models import db, Usuario, Pedido, ItemPedido
from decimal import Decimal
from dotenv import load_dotenv
import os


load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
database_url = os.getenv("DATABASE_URL", "sqlite:///projetost.db")

# Adapta a URL para usar o driver psycopg instalado.
if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://",
        "postgresql+psycopg://",
        1
    )
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1
    )

app.config["SQLALCHEMY_DATABASE_URI"] = database_url

db.init_app(app)

with app.app_context():
    db.create_all()

STATUS_PEDIDO = {
    "aguardando_pagamento": "Aguardando pagamento",
    "pago": "Pagamento confirmado",
    "em_separacao": "Em separação",
    "enviado": "Enviado",
    "entregue": "Entregue",
    "cancelado": "Cancelado"
}

PRODUTOS = {
    "CA3002": {
        "codigo": "CA3002",
        "nome": "Caneta CA3002",
        "imagem": "CA3002.jpg",
        "preco": Decimal("59.00"),
        "preco_exibicao": "59,00"
    },
    "CA3004": {
        "codigo": "CA3004",
        "nome": "Caneta CA3004",
        "imagem": "CA3004.jpg",
        "preco": Decimal("60.00"),
        "preco_exibicao": "60,00"
    },
    "CA3005": {
        "codigo": "CA3005",
        "nome": "Caneta CA3005",
        "imagem": "CA3005.jpg",
        "preco": Decimal("58.00"),
        "preco_exibicao": "58,00"
    },
    "CA3006": {
        "codigo": "CA3006",
        "nome": "Caneta CA3006",
        "imagem": "CA3006.jpg",
        "preco": Decimal("78.00"),
        "preco_exibicao": "78,00"
    },
    "CA3007": {
        "codigo": "CA3007",
        "nome": "Caneta CA3007",
        "imagem": "CA3007.jpg",
        "preco": Decimal("72.00"),
        "preco_exibicao": "72,00"
    },
    "SUPORTE": {
        "codigo": "SUPORTE",
        "nome": "Suporte para celular",
        "imagem": "suporte.jpg",
        "preco": Decimal("55.00"),
        "preco_exibicao": "55,00"
    }
}


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

@app.route("/carrinho/adicionar", methods=["POST"])
def adicionar_ao_carrinho():
    codigo = request.form.get("codigo_produto", "")
    quantidade_recebida = request.form.get("quantidade", "1")

    if codigo not in PRODUTOS:
        flash("Produto não encontrado.", "erro")
        return redirect(url_for("catalogo"))

    try:
        quantidade = max(1, int(quantidade_recebida))
    except (TypeError, ValueError):
        quantidade = 1

    # O carrinho guarda o número de pacotes de cada produto.
    carrinho_salvo = session.get("carrinho", {}).copy()
    carrinho_salvo[codigo] = int(carrinho_salvo.get(codigo, 0)) + quantidade
    session["carrinho"] = carrinho_salvo

    flash("Produto adicionado ao carrinho.", "sucesso")
    return redirect(url_for("carrinho"))

@app.route("/carrinho")
def carrinho():
    carrinho_salvo = session.get("carrinho", {})
    itens = []
    total = Decimal("0.00")

    for codigo, quantidade_salva in carrinho_salvo.items():
        produto = PRODUTOS.get(codigo)

        if produto is None:
            continue

        try:
            quantidade = max(1, int(quantidade_salva))
        except (TypeError, ValueError):
            continue

        preco_pacote = Decimal(produto["preco"])
        subtotal = preco_pacote * quantidade
        total += subtotal

        itens.append({
            "codigo": codigo,
            "nome": produto["nome"],
            "imagem": produto["imagem"],
            "quantidade": quantidade,
            "preco_pacote": preco_pacote,
            "subtotal": subtotal
        })

    return render_template("carrinho.html", itens=itens, total=total)

@app.route("/pedidos")
def pedidos():
    usuario_id = session.get("usuario_id")

    if not usuario_id:
        flash("Entre na sua conta para ver os pedidos.", "aviso")
        return redirect(url_for("login"))

    # O login salva a chave "is_admin", então a rota precisa ler a mesma chave.
    if session.get("is_admin") is True:
        lista_pedidos = Pedido.query.order_by(Pedido.criado_em.desc()).all()

        return render_template(
            "pedidos_admin.html",
            pedidos=lista_pedidos,
            status_pedido=STATUS_PEDIDO
        )

    lista_pedidos = (
        Pedido.query
        .filter_by(id_usuario=usuario_id)
        .order_by(Pedido.criado_em.desc())
        .all()
    )

    return render_template(
        "pedidos_usuario.html",
        pedidos=lista_pedidos,
        status_pedido=STATUS_PEDIDO
    )

@app.route("/catalogo")
def catalogo():
    return render_template(
        "catalogo.html",
        produtos=PRODUTOS.values()
    )
    

@app.route("/carrinho/remover/<codigo>", methods=["POST"])
def remover_do_carrinho(codigo):
    carrinho_salvo = session.get("carrinho", {}).copy()
    carrinho_salvo.pop(codigo, None)
    session["carrinho"] = carrinho_salvo

    return redirect(url_for("carrinho"))


@app.route("/finalizar-compra", methods=["POST"])
def finalizar_compra():
    usuario_id = session.get("usuario_id")

    if not usuario_id:
        flash("Entre na sua conta para continuar.", "aviso")
        return redirect(url_for("login"))

    carrinho_salvo = session.get("carrinho", {})

    if not carrinho_salvo:
        flash("Seu carrinho está vazio.", "aviso")
        return redirect(url_for("carrinho"))

    pedido = Pedido(
        id_usuario=usuario_id,
        status="aguardando_pagamento",
        total=Decimal("0.00")
    )

    total = Decimal("0.00")

    for codigo, quantidade_salva in carrinho_salvo.items():
        produto = PRODUTOS.get(codigo)

        if produto is None:
            continue

        try:
            quantidade = max(1, int(quantidade_salva))
        except (TypeError, ValueError):
            continue

        preco_pacote = Decimal(produto["preco"])
        subtotal = preco_pacote * quantidade

        pedido.itens.append(ItemPedido(
            codigo_produto=codigo,
            nome_produto=produto["nome"],
            unidades_por_pacote=100,
            quantidade_pacotes=quantidade,
            preco_pacote=preco_pacote,
            subtotal=subtotal
        ))

        total += subtotal

    if not pedido.itens:
        flash("Não encontrei produtos válidos no carrinho.", "erro")
        return redirect(url_for("carrinho"))

    pedido.total = total

    try:
        db.session.add(pedido)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("Não foi possível criar o pedido.", "erro")
        return redirect(url_for("carrinho"))

    session.pop("carrinho", None)
    flash("Pedido criado e aguardando pagamento.", "sucesso")

    return redirect(url_for("pedidos"))


@app.route("/admin/pedidos/<int:pedido_id>/status", methods=["POST"])
def atualizar_status_pedido(pedido_id):
    if session.get("is_admin") is not True:
        abort(403)

    status_novo = request.form.get("status")

    if status_novo not in STATUS_PEDIDO:
        flash("Status inválido.", "erro")
        return redirect(url_for("pedidos"))

    pedido = db.session.get(Pedido, pedido_id)

    if pedido is None:
        flash("Pedido não encontrado.", "erro")
        return redirect(url_for("pedidos"))

    pedido.status = status_novo
    db.session.commit()

    flash(f"Status do pedido #{pedido.id} atualizado.", "sucesso")
    return redirect(url_for("pedidos"))

if __name__=="__main__":
    app.run(debug=True)