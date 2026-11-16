CREATE TABLE IF NOT EXISTS categorie_produit (
  id_categorie INT AUTO_INCREMENT PRIMARY KEY,
  libelle VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS produit (
  id_produit INT AUTO_INCREMENT PRIMARY KEY,
  designation VARCHAR(150) NOT NULL,
  prix_vente DECIMAL(12,2) NOT NULL,
  id_categorie INT NOT NULL,
  CONSTRAINT fk_produit_categorie FOREIGN KEY (id_categorie)
    REFERENCES categorie_produit(id_categorie)
);
