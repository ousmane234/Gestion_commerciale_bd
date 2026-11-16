import os
import json
import pymysql
from datetime import date
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


def to_int(v, default=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def lignes_formulaire():
    """Lit les lignes (produit / quantité / prix) d'un formulaire d'achat ou de vente."""
    ids = request.form.getlist("id_produit")
    qtes = request.form.getlist("quantite")
    prix = request.form.getlist("prix")
    lignes = []
    for i, q, p in zip(ids, qtes, prix):
        if i and to_int(q) > 0 and p not in ("", None):
            lignes.append((int(i), int(q), float(p)))
    return lignes


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
    return redirect(url_for("dashboard"))


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


# ---------- FOURNISSEURS ----------
@app.route("/fournisseurs")
def fournisseurs():
    rows = query("SELECT * FROM fournisseur ORDER BY nom")
    return render_template("fournisseurs.html", fournisseurs=rows)


@app.route("/fournisseurs/ajouter", methods=["POST"])
def fournisseur_ajouter():
    nom = request.form["nom"].strip()
    if nom:
        query("INSERT INTO fournisseur (nom, telephone, adresse) VALUES (%s,%s,%s)",
              (nom, request.form.get("telephone", "").strip() or None,
               request.form.get("adresse", "").strip() or None), commit=True)
        flash("Fournisseur ajouté.", "success")
    return redirect(url_for("fournisseurs"))


@app.route("/fournisseurs/<int:id>/supprimer", methods=["POST"])
def fournisseur_supprimer(id):
    try:
        query("DELETE FROM fournisseur WHERE id_fournisseur=%s", (id,), commit=True)
        flash("Fournisseur supprimé.", "success")
    except pymysql.err.IntegrityError:
        flash("Impossible : ce fournisseur a des approvisionnements.", "danger")
    return redirect(url_for("fournisseurs"))


def produits_pour_formulaire():
    return query("SELECT id_produit, designation, prix_vente FROM produit ORDER BY designation")


# ---------- APPROVISIONNEMENTS ----------
@app.route("/approvisionnements")
def approvisionnements():
    rows = query("""SELECT a.id_appro, a.date_appro, f.nom AS fournisseur,
                           COALESCE(SUM(d.quantite*d.prix_achat),0) AS total,
                           COUNT(d.id_detail_appro) AS nb_lignes
                    FROM approvisionnement a
                    JOIN fournisseur f ON f.id_fournisseur = a.id_fournisseur
                    LEFT JOIN detail_approvisionnement d ON d.id_appro = a.id_appro
                    GROUP BY a.id_appro, a.date_appro, f.nom
                    ORDER BY a.date_appro DESC, a.id_appro DESC""")
    return render_template("approvisionnements.html", appros=rows)


@app.route("/approvisionnements/nouveau", methods=["GET", "POST"])
def appro_nouveau():
    if request.method == "POST":
        lignes = lignes_formulaire()
        if not lignes:
            flash("Ajoutez au moins une ligne valide.", "danger")
            return redirect(url_for("appro_nouveau"))
        conn = get_conn()
        try:
            conn.autocommit(False)
            with conn.cursor() as cur:
                cur.execute("INSERT INTO approvisionnement (date_appro, id_fournisseur) VALUES (%s,%s)",
                            (request.form["date_appro"], request.form["id_fournisseur"]))
                id_appro = cur.lastrowid
                for id_p, q, p in lignes:
                    cur.execute("""INSERT INTO detail_approvisionnement
                                   (id_appro, id_produit, quantite, prix_achat) VALUES (%s,%s,%s,%s)""",
                                (id_appro, id_p, q, p))
                    id_detail = cur.lastrowid
                    cur.execute("""INSERT INTO mouvement_stock
                                   (id_produit, type_mouvement, quantite, id_detail_appro)
                                   VALUES (%s,'ENTREE',%s,%s)""", (id_p, q, id_detail))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
        flash("Approvisionnement enregistré (stock mis à jour).", "success")
        return redirect(url_for("approvisionnements"))
    return render_template("appro_form.html",
                           fournisseurs=query("SELECT * FROM fournisseur ORDER BY nom"),
                           produits=produits_pour_formulaire(),
                           today=date.today().isoformat())


@app.route("/approvisionnements/<int:id>")
def appro_detail(id):
    entete = query("""SELECT a.*, f.nom AS fournisseur FROM approvisionnement a
                      JOIN fournisseur f ON f.id_fournisseur=a.id_fournisseur
                      WHERE a.id_appro=%s""", (id,), one=True)
    lignes = query("""SELECT d.*, p.designation FROM detail_approvisionnement d
                      JOIN produit p ON p.id_produit=d.id_produit WHERE d.id_appro=%s""", (id,))
    return render_template("appro_detail.html", a=entete, lignes=lignes)


# ---------- VENTES ----------
@app.route("/ventes")
def ventes():
    rows = query("""SELECT v.id_vente, v.date_vente,
                           COALESCE(SUM(d.quantite*d.prix_unitaire),0) AS total,
                           COUNT(d.id_detail_vente) AS nb_lignes
                    FROM vente v LEFT JOIN detail_vente d ON d.id_vente = v.id_vente
                    GROUP BY v.id_vente, v.date_vente
                    ORDER BY v.date_vente DESC, v.id_vente DESC""")
    return render_template("ventes.html", ventes=rows)


@app.route("/ventes/nouvelle", methods=["GET", "POST"])
def vente_nouvelle():
    if request.method == "POST":
        lignes = lignes_formulaire()
        if not lignes:
            flash("Ajoutez au moins une ligne valide.", "danger")
            return redirect(url_for("vente_nouvelle"))
        conn = get_conn()
        try:
            conn.autocommit(False)
            with conn.cursor() as cur:
                # vérification du stock disponible (total par produit)
                demande = {}
                for id_p, q, _ in lignes:
                    demande[id_p] = demande.get(id_p, 0) + q
                for id_p, q in demande.items():
                    cur.execute("SELECT stock_actuel, designation FROM v_stock WHERE id_produit=%s", (id_p,))
                    r = cur.fetchone()
                    if r is None or r["stock_actuel"] < q:
                        dispo = r["stock_actuel"] if r else 0
                        nom = r["designation"] if r else id_p
                        conn.rollback()
                        flash(f"Stock insuffisant pour « {nom} » : {dispo} disponible(s), {q} demandé(s).", "danger")
                        return redirect(url_for("vente_nouvelle"))
                cur.execute("INSERT INTO vente (date_vente) VALUES (%s)", (request.form["date_vente"],))
                id_vente = cur.lastrowid
                for id_p, q, p in lignes:
                    cur.execute("""INSERT INTO detail_vente
                                   (id_vente, id_produit, quantite, prix_unitaire) VALUES (%s,%s,%s,%s)""",
                                (id_vente, id_p, q, p))
                    id_detail = cur.lastrowid
                    cur.execute("""INSERT INTO mouvement_stock
                                   (id_produit, type_mouvement, quantite, id_detail_vente)
                                   VALUES (%s,'SORTIE',%s,%s)""", (id_p, q, id_detail))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
        flash("Vente enregistrée (stock mis à jour).", "success")
        return redirect(url_for("ventes"))
    return render_template("vente_form.html", produits=produits_pour_formulaire(),
                           today=date.today().isoformat())


@app.route("/ventes/<int:id>")
def vente_detail(id):
    entete = query("SELECT * FROM vente WHERE id_vente=%s", (id,), one=True)
    lignes = query("""SELECT d.*, p.designation FROM detail_vente d
                      JOIN produit p ON p.id_produit=d.id_produit WHERE d.id_vente=%s""", (id,))
    return render_template("vente_detail.html", v=entete, lignes=lignes)


# ---------- DÉPENSES ----------
@app.route("/depenses")
def depenses():
    rows = query("SELECT * FROM depense ORDER BY date_depense DESC, id_depense DESC")
    total = sum(r["montant"] for r in rows)
    return render_template("depenses.html", depenses=rows, total=total, today=date.today().isoformat())


@app.route("/depenses/ajouter", methods=["POST"])
def depense_ajouter():
    query("INSERT INTO depense (date_depense, libelle, montant) VALUES (%s,%s,%s)",
          (request.form["date_depense"], request.form["libelle"].strip(), request.form["montant"]),
          commit=True)
    flash("Dépense enregistrée.", "success")
    return redirect(url_for("depenses"))


@app.route("/depenses/<int:id>/supprimer", methods=["POST"])
def depense_supprimer(id):
    query("DELETE FROM depense WHERE id_depense=%s", (id,), commit=True)
    flash("Dépense supprimée.", "success")
    return redirect(url_for("depenses"))


# ---------- STOCK ----------
@app.route("/stock")
def stock():
    rows = query("""SELECT s.id_produit, s.designation, s.stock_actuel, c.libelle
                    FROM v_stock s JOIN produit p ON p.id_produit = s.id_produit
                    JOIN categorie_produit c ON c.id_categorie = p.id_categorie
                    ORDER BY s.designation""")
    return render_template("stock.html", stock=rows)


# ---------- TABLEAU DE BORD ----------
@app.route("/dashboard")
def dashboard():
    ca = query("SELECT COALESCE(SUM(quantite*prix_unitaire),0) AS t FROM detail_vente", one=True)["t"]
    achats = query("SELECT COALESCE(SUM(quantite*prix_achat),0) AS t FROM detail_approvisionnement", one=True)["t"]
    dep = query("SELECT COALESCE(SUM(montant),0) AS t FROM depense", one=True)["t"]
    marge = query("""SELECT COALESCE(SUM(d.quantite * (d.prix_unitaire -
                        COALESCE((SELECT SUM(a.quantite*a.prix_achat)/SUM(a.quantite)
                                  FROM detail_approvisionnement a WHERE a.id_produit = d.id_produit), 0))), 0) AS t
                     FROM detail_vente d""", one=True)["t"]
    mensuel = query("""SELECT DATE_FORMAT(v.date_vente, '%%Y-%%m') AS mois,
                              SUM(d.quantite*d.prix_unitaire) AS ca
                       FROM vente v JOIN detail_vente d ON d.id_vente = v.id_vente
                       GROUP BY mois ORDER BY mois""")
    top = query("""SELECT p.designation, SUM(d.quantite) AS qte, SUM(d.quantite*d.prix_unitaire) AS ca
                   FROM detail_vente d JOIN produit p ON p.id_produit = d.id_produit
                   GROUP BY p.id_produit, p.designation ORDER BY ca DESC LIMIT 5""")
    return render_template("dashboard.html", ca=ca, achats=achats, depenses=dep,
                           marge_brute=marge, resultat=ca - achats - dep,
                           labels=json.dumps([m["mois"] for m in mensuel]),
                           valeurs=json.dumps([float(m["ca"]) for m in mensuel]), top=top)


if __name__ == "__main__":
    app.run(debug=True)
