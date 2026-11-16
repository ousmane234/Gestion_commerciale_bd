import os
import pymysql
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-change-me")


def get_conn():
    """Connexion MySQL : les paramètres viennent des variables d'environnement."""
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", 3306)),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
        connect_timeout=15,
    )


def query(sql, params=(), one=False, commit=False):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if commit:
                return cur.lastrowid
            rows = cur.fetchall()
            return (rows[0] if rows else None) if one else rows
    finally:
        conn.close()


def init_db():
    """Crée les tables si elles n'existent pas (lit schema.sql)."""
    path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(path, encoding="utf-8") as f:
        statements = [s.strip() for s in f.read().split(";") if s.strip()]
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            for s in statements:
                cur.execute(s)
    finally:
        conn.close()


try:
    init_db()
except Exception as e:  # l'app démarre quand même ; l'erreur s'affichera dans les logs
    print("init_db a échoué :", e)


@app.route("/")
def index():
    return redirect(url_for("produits"))


# ---------- CATÉGORIES ----------
@app.route("/categories")
def categories():
    rows = query("SELECT * FROM categorie_produit ORDER BY libelle")
    return render_template("categories.html", categories=rows)


@app.route("/categories/ajouter", methods=["POST"])
def categorie_ajouter():
    libelle = request.form["libelle"].strip()
    if libelle:
        query("INSERT INTO categorie_produit (libelle) VALUES (%s)", (libelle,), commit=True)
        flash("Catégorie ajoutée.", "success")
    return redirect(url_for("categories"))


@app.route("/categories/<int:id>/modifier", methods=["GET", "POST"])
def categorie_modifier(id):
    if request.method == "POST":
        query("UPDATE categorie_produit SET libelle=%s WHERE id_categorie=%s",
              (request.form["libelle"].strip(), id), commit=True)
        flash("Catégorie modifiée.", "success")
        return redirect(url_for("categories"))
    cat = query("SELECT * FROM categorie_produit WHERE id_categorie=%s", (id,), one=True)
    return render_template("categorie_edit.html", cat=cat)


@app.route("/categories/<int:id>/supprimer", methods=["POST"])
def categorie_supprimer(id):
    try:
        query("DELETE FROM categorie_produit WHERE id_categorie=%s", (id,), commit=True)
        flash("Catégorie supprimée.", "success")
    except pymysql.err.IntegrityError:
        flash("Impossible : cette catégorie contient encore des produits.", "danger")
    return redirect(url_for("categories"))


# ---------- PRODUITS ----------
@app.route("/produits")
def produits():
    rows = query("""SELECT p.id_produit, p.designation, p.prix_vente, c.libelle
                    FROM produit p JOIN categorie_produit c ON c.id_categorie = p.id_categorie
                    ORDER BY p.designation""")
    cats = query("SELECT * FROM categorie_produit ORDER BY libelle")
    return render_template("produits.html", produits=rows, categories=cats)


@app.route("/produits/ajouter", methods=["POST"])
def produit_ajouter():
    query("INSERT INTO produit (designation, prix_vente, id_categorie) VALUES (%s,%s,%s)",
          (request.form["designation"].strip(), request.form["prix_vente"],
           request.form["id_categorie"]), commit=True)
    flash("Produit ajouté.", "success")
    return redirect(url_for("produits"))


@app.route("/produits/<int:id>/modifier", methods=["GET", "POST"])
def produit_modifier(id):
    if request.method == "POST":
        query("""UPDATE produit SET designation=%s, prix_vente=%s, id_categorie=%s
                 WHERE id_produit=%s""",
              (request.form["designation"].strip(), request.form["prix_vente"],
               request.form["id_categorie"], id), commit=True)
        flash("Produit modifié.", "success")
        return redirect(url_for("produits"))
    p = query("SELECT * FROM produit WHERE id_produit=%s", (id,), one=True)
    cats = query("SELECT * FROM categorie_produit ORDER BY libelle")
    return render_template("produit_edit.html", p=p, categories=cats)


@app.route("/produits/<int:id>/supprimer", methods=["POST"])
def produit_supprimer(id):
    query("DELETE FROM produit WHERE id_produit=%s", (id,), commit=True)
    flash("Produit supprimé.", "success")
    return redirect(url_for("produits"))


if __name__ == "__main__":
    app.run(debug=True)
