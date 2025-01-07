# README

Ce document fournit une description des fichiers Jupyter Notebook inclus dans ce projet, ainsi que leurs objectifs et les étapes principales de leur utilisation. Ce projet traite des données de l'enquête EHCVM 2021 pour analyser la pauvreté à travers des données d'enquête et d'images satellitaires.

## Structure des fichiers

### 1. **Traitement des données enquêtes 2021.ipynb**
   - **Objectif :** Ce script prépare et nettoie les données d'enquête EHCVM 2021 pour les rendre exploitables.
   - **Principales étapes :**
     1. Importation et vérification des données.
     2. Traitement des valeurs manquantes et des doublons.
     3. Création de nouvelles variables pour l'analyse.
     4. Exportation des données nettoyées.

### 2. **EHCVM 2021 Ménages Script de Téléchargement d'Images Satellites pour Analyse Géospatiale à Partir de Coordonnées GPS.ipynb**
   - **Objectif :** Télécharger des images satellites à partir des coordonnées GPS des ménages enquêtés.
   - **Principales étapes :**
     1. Lecture des coordonnées GPS des ménages.
     2. Accès à l'API du fournisseur d'images satellites.
     3. Téléchargement des images avec des critères prédéfinis (résolution, couverture nuageuse, etc.).
     4. Sauvegarde des images dans un répertoire spécifique.

### 3. **EHCVM 2021 Insertion des noms des images téléchargées dans une Data frame contenant les données d'enquêtes.ipynb**
   - **Objectif :** Associer les images téléchargées aux données d'enquête.
   - **Principales étapes :**
     1. Création d'une colonne dans le DataFrame pour les noms d'images.
     2. Liaison entre les images et les ménages en fonction des coordonnées GPS.
     3. Exportation du DataFrame enrichi.

### 4. **Extraction de caractéristiques VGG16 fullyConv_sans_augm_couche_nongelee_batch_16_6k.ipynb**
   - **Objectif :** Extraire des caractéristiques des images satellites à l'aide du modèle VGG16 préentraîné.
   - **Principales étapes :**
     1. Chargement des images prétraitées.
     2. Utilisation de VGG16 pour extraire des vecteurs de caractéristiques.
     3. Sauvegarde des caractéristiques pour une analyse ultérieure.

### 5. **Prédiction de la pauvreté EHCVM 2021 avec la régression logistique et le Calcul des Taux de Pauvreté fullyConv_sans_augm_couche_nongelee_batch_16.ipynb**
   - **Objectif :** Prédire les taux de pauvreté à l'aide des données extraites et calculer les indicateurs de pauvreté.
   - **Principales étapes :**
     1. Chargement des caractéristiques extraites.
     2. Entraînement et évaluation de modèles de régression logistique.
     3. Calcul des taux de pauvreté prédits et comparaison avec les taux réels.

### 6. **Cartographie EHCVM 2021 des Incidences de Pauvreté Réelle et Prédite par Région.ipynb**
   - **Objectif :** Générer des cartes thématiques montrant les incidences de pauvreté par région.
   - **Principales étapes :**
     1. Importation des résultats prédits et réels.
     2. Association des données de pauvreté avec les frontières régionales.
     3. Génération de cartes à l'aide d'outils comme Matplotlib, Geopandas, ou Folium.

## Prérequis
- Python 3.8 ou version ultérieure.
- Bibliothèques nécessaires : pandas, numpy, matplotlib, tensorflow, keras, geopandas, folium, et requests.
- Accès à l'API du fournisseur d'images satellitaires.

## Instructions d'exécution
1. Exécutez les fichiers dans l'ordre numéroté pour garantir une progression logique.
2. Assurez-vous que les fichiers d'entrée (données d'enquête, coordonnées GPS, etc.) sont correctement formatés.
3. Modifiez les chemins et les configurations selon votre environnement.
4. Révisez les sorties à chaque étape pour valider les résultats.

## Contact
Pour toute question ou support technique, veuillez contacter :
- **Nom :** Koné Kinin Mamdou
- **Organisation :** Agence Nationale de la Statistique (ANStat) de Côte d'Ivoire

---

