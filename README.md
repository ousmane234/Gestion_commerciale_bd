# Gestion commerciale – version complète
Flask + MySQL (FreeDB) + Bootstrap, déployé sur Render.
Modules : catégories, produits, fournisseurs, approvisionnements, ventes, dépenses, stock, tableau de bord.

Variables d'environnement (Render > Environment) : DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, SECRET_KEY
Build : `pip install -r requirements.txt` — Démarrage : `gunicorn app:app`

Au démarrage, l'application exécute schema.sql (CREATE TABLE IF NOT EXISTS).
donnees_test.sql est facultatif (données d'exemple, à exécuter à la main).
