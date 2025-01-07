# README

Ce document fournit une description des fichiers Jupyter Notebook inclus dans ce projet, ainsi que leurs objectifs et les étapes principales de leur utilisation. Ce projet porte sur l’analyse de la consommation par tête et de la pauvreté à l’aide de données d’images satellites et d’apprentissage automatique.

## Structure des fichiers

### 1. **Creation de dataframe avec nom Image Africa sampled with images.ipynb**
   - **Objectif :** Créer un DataFrame contenant les noms des images satellites et les coordonnées correspondantes des zones échantillonnées en Afrique.
   - **Principales étapes :**
     1. Lecture des coordonnées GPS des zones ciblées.
     2. Liaison entre les images satellites et leurs coordonnées.
     3. Exportation du DataFrame final pour une utilisation ultérieure.

### 2. **Train_eval_fullyConv_sans_augm_couche_nongelée.ipynb**
   - **Objectif :** Entraîner et évaluer un modèle convolutionnel prédit sur des images satellites en utilisant un modèle pré-entraîné avec certaines couches non gelées.
   - **Principales étapes :**
     1. Préparation des données d’entraînement et de validation.
     2. Entraînement du modèle sur les données.
     3. Évaluation des performances du modèle à l’aide de métriques comme la précision et la perte.

### 3. **Extraction de caractéristiques VGG16 fullyConv_sans_augm_couche_nongelee_batch_16.ipynb**
   - **Objectif :** Extraire des caractéristiques des images à l’aide d’un modèle VGG16 pré-entraîné.
   - **Principales étapes :**
     1. Chargement des images satellites.
     2. Utilisation de VGG16 pour obtenir des vecteurs de caractéristiques.
     3. Sauvegarde des caractéristiques pour une analyse ou une modélisation future.

### 4. **Prédiction de la Consommation par tête et le Calcul des Taux de Pauvreté fullyConv_sans_augm_couche_nongelee_batch_16.ipynb**
   - **Objectif :** Prédire la consommation par tête et calculer les taux de pauvreté à l’aide des caractéristiques extraites.
   - **Principales étapes :**
     1. Chargement des caractéristiques des images satellites.
     2. Prédiction des valeurs de consommation par ménage.
     3. Calcul et analyse des taux de pauvreté.

### 5. **Prédiction de la pauvreté avec la régression logistique et le Calcul des Taux de Pauvreté fullyConv_sans_augm_couche_nongelee_batch_16.ipynb**
   - **Objectif :** Utiliser la régression logistique pour prédire les taux de pauvreté et comparer les prédictions aux résultats réels.
   - **Principales étapes :**
     1. Entraînement d’un modèle de régression logistique sur les données extraites.
     2. Analyse des résultats et validation des prédictions.

### 6. **Cartographie des Incidences de Pauvreté Réelle et Prédite par Région.ipynb**
   - **Objectif :** Créer des cartes illustrant les taux de pauvreté réels et prédits pour chaque région.
   - **Principales étapes :**
     1. Intégration des données prédites et réelles avec les frontières régionales.
     2. Visualisation géographique des taux de pauvreté à l’aide d’outils comme Geopandas et Matplotlib.

## Prérequis
- Python 3.8 ou version ultérieure.
- Bibliothèques Python : pandas, numpy, matplotlib, tensorflow, keras, geopandas, folium, requests.
- Accès aux données d’images satellites et à l’API Planet (ou autre fournisseur).

## Instructions d’exécution
1. Exécutez les fichiers dans l’ordre numéroté pour garantir une progression logique.
2. Assurez-vous que les fichiers d’entrée (images, données socio-économiques) sont présents et correctement formatés.
3. Modifiez les chemins des fichiers et les configurations selon votre environnement.
4. Vérifiez les résultats à chaque étape pour garantir la cohérence des analyses.

## Contact
Pour toute question ou assistance technique, veuillez contacter :
- **Nom :** Koné Kinin Mamdou
- **Organisation :** Agence Nationale de la Statistique (ANStat) de Côte d'Ivoire

---

