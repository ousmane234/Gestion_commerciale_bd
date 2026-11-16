-- =====================================================================
-- Gestion commerciale (secteur informel) - Schéma complet (10 tables)
-- Compatible MySQL / FreeDB. Réexécutable sans risque (IF NOT EXISTS).
-- Les tables categorie_produit et produit sont identiques à la V1 :
-- l'application déployée continue donc de fonctionner.
-- =====================================================================

-- 1. Catégories
CREATE TABLE IF NOT EXISTS categorie_produit (
  id_categorie INT AUTO_INCREMENT PRIMARY KEY,
  libelle VARCHAR(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Produits
CREATE TABLE IF NOT EXISTS produit (
  id_produit INT AUTO_INCREMENT PRIMARY KEY,
  designation VARCHAR(150) NOT NULL,
  prix_vente DECIMAL(12,2) NOT NULL,
  id_categorie INT NOT NULL,
  CONSTRAINT fk_produit_categorie FOREIGN KEY (id_categorie)
    REFERENCES categorie_produit(id_categorie)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Fournisseurs
CREATE TABLE IF NOT EXISTS fournisseur (
  id_fournisseur INT AUTO_INCREMENT PRIMARY KEY,
  nom VARCHAR(150) NOT NULL,
  telephone VARCHAR(30),
  adresse VARCHAR(255)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Utilisateurs (comptes et accès)
CREATE TABLE IF NOT EXISTS utilisateur (
  id_utilisateur INT AUTO_INCREMENT PRIMARY KEY,
  nom VARCHAR(100) NOT NULL,
  login VARCHAR(50) NOT NULL UNIQUE,
  mot_de_passe_hash VARCHAR(255) NOT NULL,
  role VARCHAR(20) NOT NULL DEFAULT 'commercant',
  date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Approvisionnements (en-tête)
CREATE TABLE IF NOT EXISTS approvisionnement (
  id_appro INT AUTO_INCREMENT PRIMARY KEY,
  date_appro DATE NOT NULL,
  id_fournisseur INT NOT NULL,
  id_utilisateur INT NULL,
  CONSTRAINT fk_appro_fournisseur FOREIGN KEY (id_fournisseur)
    REFERENCES fournisseur(id_fournisseur),
  CONSTRAINT fk_appro_utilisateur FOREIGN KEY (id_utilisateur)
    REFERENCES utilisateur(id_utilisateur) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Détail des approvisionnements (lignes)
CREATE TABLE IF NOT EXISTS detail_approvisionnement (
  id_detail_appro INT AUTO_INCREMENT PRIMARY KEY,
  id_appro INT NOT NULL,
  id_produit INT NOT NULL,
  quantite INT NOT NULL CHECK (quantite > 0),
  prix_achat DECIMAL(12,2) NOT NULL CHECK (prix_achat >= 0),
  CONSTRAINT fk_da_appro FOREIGN KEY (id_appro)
    REFERENCES approvisionnement(id_appro) ON DELETE CASCADE,
  CONSTRAINT fk_da_produit FOREIGN KEY (id_produit)
    REFERENCES produit(id_produit)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. Ventes (en-tête)
CREATE TABLE IF NOT EXISTS vente (
  id_vente INT AUTO_INCREMENT PRIMARY KEY,
  date_vente DATE NOT NULL,
  id_utilisateur INT NULL,
  CONSTRAINT fk_vente_utilisateur FOREIGN KEY (id_utilisateur)
    REFERENCES utilisateur(id_utilisateur) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. Détail des ventes (lignes)
CREATE TABLE IF NOT EXISTS detail_vente (
  id_detail_vente INT AUTO_INCREMENT PRIMARY KEY,
  id_vente INT NOT NULL,
  id_produit INT NOT NULL,
  quantite INT NOT NULL CHECK (quantite > 0),
  prix_unitaire DECIMAL(12,2) NOT NULL CHECK (prix_unitaire >= 0),
  CONSTRAINT fk_dv_vente FOREIGN KEY (id_vente)
    REFERENCES vente(id_vente) ON DELETE CASCADE,
  CONSTRAINT fk_dv_produit FOREIGN KEY (id_produit)
    REFERENCES produit(id_produit)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9. Dépenses
CREATE TABLE IF NOT EXISTS depense (
  id_depense INT AUTO_INCREMENT PRIMARY KEY,
  date_depense DATE NOT NULL,
  libelle VARCHAR(150) NOT NULL,
  montant DECIMAL(12,2) NOT NULL CHECK (montant >= 0),
  id_utilisateur INT NULL,
  CONSTRAINT fk_depense_utilisateur FOREIGN KEY (id_utilisateur)
    REFERENCES utilisateur(id_utilisateur) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 10. Mouvements de stock (entrées et sorties)
CREATE TABLE IF NOT EXISTS mouvement_stock (
  id_mouvement INT AUTO_INCREMENT PRIMARY KEY,
  date_mouvement DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  id_produit INT NOT NULL,
  type_mouvement ENUM('ENTREE','SORTIE') NOT NULL,
  quantite INT NOT NULL CHECK (quantite > 0),
  id_detail_appro INT NULL,
  id_detail_vente INT NULL,
  CONSTRAINT fk_ms_produit FOREIGN KEY (id_produit)
    REFERENCES produit(id_produit),
  CONSTRAINT fk_ms_da FOREIGN KEY (id_detail_appro)
    REFERENCES detail_approvisionnement(id_detail_appro) ON DELETE SET NULL,
  CONSTRAINT fk_ms_dv FOREIGN KEY (id_detail_vente)
    REFERENCES detail_vente(id_detail_vente) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Vue utile : stock actuel par produit
CREATE OR REPLACE VIEW v_stock AS
SELECT p.id_produit, p.designation,
       COALESCE(SUM(CASE WHEN m.type_mouvement='ENTREE' THEN m.quantite
                         WHEN m.type_mouvement='SORTIE' THEN -m.quantite END), 0) AS stock_actuel
FROM produit p
LEFT JOIN mouvement_stock m ON m.id_produit = p.id_produit
GROUP BY p.id_produit, p.designation;
