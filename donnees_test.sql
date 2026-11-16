-- Données de test (à exécuter après schema_complet.sql)
INSERT INTO categorie_produit (libelle) VALUES ('Boissons'), ('Alimentation'), ('Hygiène');

INSERT INTO produit (designation, prix_vente, id_categorie) VALUES
  ('Jus de bissap 1L', 1000, 1),
  ('Sac de riz 25 kg', 15000, 2),
  ('Savon de Marseille', 500, 3);

INSERT INTO fournisseur (nom, telephone, adresse) VALUES
  ('Grossiste Sandaga', '771234567', 'Marché Sandaga, Dakar'),
  ('Boulangerie Thiès', '778765432', 'Thiès');

INSERT INTO utilisateur (nom, login, mot_de_passe_hash, role) VALUES
  ('Administrateur', 'admin', 'A_REMPLACER_PAR_UN_HASH', 'admin');

INSERT INTO approvisionnement (date_appro, id_fournisseur, id_utilisateur) VALUES (CURDATE(), 1, 1);
INSERT INTO detail_approvisionnement (id_appro, id_produit, quantite, prix_achat) VALUES
  (1, 1, 50, 700), (1, 2, 10, 12500);
INSERT INTO mouvement_stock (id_produit, type_mouvement, quantite, id_detail_appro) VALUES
  (1, 'ENTREE', 50, 1), (2, 'ENTREE', 10, 2);

INSERT INTO vente (date_vente, id_utilisateur) VALUES (CURDATE(), 1);
INSERT INTO detail_vente (id_vente, id_produit, quantite, prix_unitaire) VALUES
  (1, 1, 5, 1000), (1, 2, 1, 15000);
INSERT INTO mouvement_stock (id_produit, type_mouvement, quantite, id_detail_vente) VALUES
  (1, 'SORTIE', 5, 1), (2, 'SORTIE', 1, 2);

INSERT INTO depense (date_depense, libelle, montant, id_utilisateur) VALUES
  (CURDATE(), 'Transport', 3000, 1), (CURDATE(), 'Électricité', 5000, 1);
