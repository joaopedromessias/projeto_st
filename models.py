from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from decimal import Decimal

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    sobrenome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    pedidos = db.relationship(
        "Pedido",
        back_populates="usuario"
    )
    
class Pedido(db.Model):
    __tablename__="pedido"
    
    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="aguardando_pagamento")    
    total = db.Column(db.Numeric(10, 2), nullable=False, default = Decimal("0.00") )
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.now)
    usuario = db.relationship("Usuario", back_populates="pedidos")
    itens = db.relationship("ItemPedido", back_populates="pedido", cascade="all, delete-orphan")

class ItemPedido(db.Model):
    __tablename__="item_pedido"
    
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedido.id"), nullable=False)
    codigo_produto = db.Column(db.String(30), nullable=False)
    nome_produto = db.Column(db.String(30), nullable=False)
    unidades_por_pacote = db.Column(db.Integer, nullable=False, default=100)
    quantidade_pacotes = db.Column(db.Integer, nullable=False)
    preco_pacote = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    pedido = db.relationship("Pedido", back_populates="itens")
    
    