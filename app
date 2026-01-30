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

class Post(db.Model):
    id = db.Column(db.String, primary_key=True)
    autor = db.Column(db.String, nullable=False)
    autor_id = db.Column(db.String, nullable=False)
    texto = db.Column(db.Text, nullable=False)
    data = db.Column(db.String, nullable=False)

class Comment(db.Model):
    id = db.Column(db.String, primary_key=True)
    post_id = db.Column(db.String, nullable=False)
    autor = db.Column(db.String, nullable=False)
    autor_id = db.Column(db.String, nullable=False)
    texto = db.Column(db.Text, nullable=False)
    data = db.Column(db.String, nullable=False)

class Like(db.Model):
    id = db.Column(db.String, primary_key=True)
    post_id = db.Column(db.String, nullable=False)
    user_id = db.Column(db.String, nullable=False)

# ================= CRIAR TABELAS =================
with app.app_context():
    db.create_all()

# ================= POSTS =================

@app.route("/posts", methods=["GET"])
def listar_posts():
    posts = Post.query.order_by(Post.data.desc()).all()
    resultado = []

    for p in posts:
        comentarios = Comment.query.filter_by(post_id=p.id).count()
        likes = Like.query.filter_by(post_id=p.id).count()

        resultado.append({
            "id": p.id,
            "autor": p.autor,
            "autor_id": p.autor_id,
            "texto": p.texto,
            "data": p.data,
            "likes": likes,
            "comentarios": comentarios
        })

    return jsonify(resultado)


@app.route("/posts", methods=["POST"])
def criar_post():
    data = request.get_json()

    post = Post(
        id=str(uuid.uuid4()),
        autor=data["autor"],
        autor_id=data["autor_id"],
        texto=data["texto"],
        data=datetime.now().strftime("%d/%m/%Y %H:%M")
    )

    db.session.add(post)
    db.session.commit()

    return jsonify({"status": "ok", "id": post.id})


@app.route("/posts/<post_id>", methods=["DELETE"])
def apagar_post(post_id):
    Post.query.filter_by(id=post_id).delete()
    Comment.query.filter_by(post_id=post_id).delete()
    Like.query.filter_by(post_id=post_id).delete()
    db.session.commit()

    return jsonify({"status": "ok"})

# ================= COMENTÁRIOS =================

@app.route("/posts/<post_id>/comments", methods=["GET"])
def listar_comentarios(post_id):
    comentarios = Comment.query.filter_by(post_id=post_id).all()
    return jsonify([{
        "id": c.id,
        "autor": c.autor,
        "autor_id": c.autor_id,
        "texto": c.texto,
        "data": c.data
    } for c in comentarios])


@app.route("/posts/<post_id>/comments", methods=["POST"])
def criar_comentario(post_id):
    data = request.get_json()

    c = Comment(
        id=str(uuid.uuid4()),
        post_id=post_id,
        autor=data["autor"],
        autor_id=data["autor_id"],
        texto=data["texto"],
        data=datetime.now().strftime("%d/%m/%Y %H:%M")
    )

    db.session.add(c)
    db.session.commit()

    return jsonify({"status": "ok"})


@app.route("/posts/<post_id>/comments/<comment_id>", methods=["DELETE"])
def apagar_comentario(post_id, comment_id):
    Comment.query.filter_by(id=comment_id, post_id=post_id).delete()
    db.session.commit()
    return jsonify({"status": "ok"})

# ================= LIKES =================

@app.route("/posts/<post_id>/like", methods=["POST"])
def toggle_like(post_id):
    data = request.get_json()
    user_id = data["user_id"]

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
