from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import uuid
import os

# ================= APP =================
app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# ================= CONFIG =================
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "social.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ================= DB =================
db = SQLAlchemy(app)

# ================= MODELOS =================

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String, primary_key=True)
    username = db.Column(db.String, nullable=False)
    apelido = db.Column(db.String, nullable=True)
    foto = db.Column(db.String, nullable=True)


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.String, primary_key=True)
    autor_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    imagem = db.Column(db.String, nullable=True)
    data = db.Column(db.String, nullable=False)


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.String, primary_key=True)
    post_id = db.Column(db.String, db.ForeignKey("posts.id"), nullable=False)
    autor_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    data = db.Column(db.String, nullable=False)


class Like(db.Model):
    __tablename__ = "likes"

    id = db.Column(db.String, primary_key=True)
    post_id = db.Column(db.String, db.ForeignKey("posts.id"), nullable=False)
    user_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)

# ================= CRIAR TABELAS =================
with app.app_context():
    db.create_all()

# ================= USERS (AUTO-CREATE) =================
def garantir_user(user_id):
    user = User.query.filter_by(id=user_id).first()
    if not user:
        user = User(
            id=user_id,
            username="Utilizador",
            apelido="",
            foto=None
        )
        db.session.add(user)
        db.session.commit()
    return user

# ================= POSTS =================

@app.route("/posts", methods=["GET"])
def listar_posts():
    posts = Post.query.order_by(Post.data.desc()).all()
    resultado = []

    for p in posts:
        user = User.query.filter_by(id=p.autor_id).first()

        autor = {
            "id": p.autor_id,
            "username": "Desconhecido",
            "apelido": "",
            "foto": None
        }

        if user:
            autor = {
                "id": user.id,
                "username": user.username,
                "apelido": user.apelido,
                "foto": user.foto
            }

        resultado.append({
            "id": p.id,
            "texto": p.texto,
            "imagem_post": p.imagem,
            "data": p.data,
            "likes": Like.query.filter_by(post_id=p.id).count(),
            "comentarios": Comment.query.filter_by(post_id=p.id).count(),
            "autor": autor
        })

    return jsonify(resultado)

# ================= CRIAR POST =================

@app.route("/posts", methods=["POST"])
def criar_post():
    data = request.get_json()

    if not data or "autor_id" not in data or "texto" not in data:
        return jsonify({"error": "Dados inválidos"}), 400

    garantir_user(data["autor_id"])

    post = Post(
        id=str(uuid.uuid4()),
        autor_id=data["autor_id"],
        texto=data["texto"],
        imagem=data.get("imagem"),
        data=datetime.now().strftime("%d/%m/%Y %H:%M")
    )

    db.session.add(post)
    db.session.commit()

    return jsonify({"status": "ok", "id": post.id})

# ================= APAGAR POST =================

@app.route("/posts/<post_id>", methods=["DELETE"])
def apagar_post(post_id):
    Comment.query.filter_by(post_id=post_id).delete()
    Like.query.filter_by(post_id=post_id).delete()
    Post.query.filter_by(id=post_id).delete()
    db.session.commit()
    return jsonify({"status": "ok"})

# ================= COMENTÁRIOS =================

@app.route("/posts/<post_id>/comments", methods=["GET"])
def listar_comentarios(post_id):
    comentarios = Comment.query.filter_by(post_id=post_id).all()
    resultado = []

    for c in comentarios:
        user = User.query.filter_by(id=c.autor_id).first()

        autor = {
            "id": c.autor_id,
            "username": "Desconhecido",
            "apelido": "",
            "foto": None
        }

        if user:
            autor = {
                "id": user.id,
                "username": user.username,
                "apelido": user.apelido,
                "foto": user.foto
            }

        resultado.append({
            "id": c.id,
            "texto": c.texto,
            "data": c.data,
            "autor": autor
        })

    return jsonify(resultado)


@app.route("/posts/<post_id>/comments", methods=["POST"])
def criar_comentario(post_id):
    data = request.get_json()

    if not data or "autor_id" not in data or "texto" not in data:
        return jsonify({"error": "Dados inválidos"}), 400

    garantir_user(data["autor_id"])

    comentario = Comment(
        id=str(uuid.uuid4()),
        post_id=post_id,
        autor_id=data["autor_id"],
        texto=data["texto"],
        data=datetime.now().strftime("%d/%m/%Y %H:%M")
    )

    db.session.add(comentario)
    db.session.commit()

    return jsonify({"status": "ok"})

# ================= APAGAR COMENTÁRIO =================

@app.route("/posts/<post_id>/comments/<comment_id>", methods=["DELETE"])
def apagar_comentario(post_id, comment_id):
    Comment.query.filter_by(id=comment_id, post_id=post_id).delete()
    db.session.commit()
    return jsonify({"status": "ok"})

# ================= LIKES =================

@app.route("/posts/<post_id>/like", methods=["POST"])
def toggle_like(post_id):
    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id obrigatório"}), 400

    garantir_user(user_id)

    existente = Like.query.filter_by(post_id=post_id, user_id=user_id).first()

    if existente:
        db.session.delete(existente)
        db.session.commit()
        return jsonify({"liked": False})

    like = Like(
        id=str(uuid.uuid4()),
        post_id=post_id,
        user_id=user_id
    )

    db.session.add(like)
    db.session.commit()
    return jsonify({"liked": True})

# ================= START =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
