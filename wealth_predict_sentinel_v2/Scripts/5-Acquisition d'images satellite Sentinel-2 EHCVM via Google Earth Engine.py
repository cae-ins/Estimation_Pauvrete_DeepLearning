
# 2019 couverture nuageuse 50% - il y'a plus d'image disponibles en 2019 qu'en 2018 pour former une mosaîque médiane des pixels

# Script de téléchargement automatique d'images Sentinel-2 pour les tuiles EHCVM
# Configuration initiale
import ee
import os
import requests
import numpy as np
import pandas as pd
from PIL import Image
import rasterio
from io import BytesIO
from tqdm import tqdm
import time
import warnings
warnings.filterwarnings('ignore')

def authenticate_and_initialize():
    """Authentification et initialisation de Google Earth Engine"""
    try:
        ee.Authenticate()
        ee.Initialize(project='') #Entrez le nom du projet dans les griffes ''
        print("✅ Authentification GEE réussie")
        return True
    except Exception as e:
        print(f"❌ Erreur d'authentification GEE: {e}")
        return False

def mask_s2_clouds(image):
    """Fonction de masquage des nuages/ombres pour Sentinel-2"""
    qa = image.select('QA60')
    cloud_mask = 1 << 10
    shadow_mask = 1 << 11
    mask = qa.bitwiseAnd(cloud_mask).eq(0).And(qa.bitwiseAnd(shadow_mask).eq(0))
    return image.updateMask(mask)

def save_as_png(data, output_path, stretch=True):
    """Fonction de conversion et sauvegarde en PNG"""
    try:
        with rasterio.open(data) as src:
            # Lire les bandes (ordre: R, G, B)
            r = src.read(1)
            g = src.read(2)
            b = src.read(3)
            
            # Combiner en image RGB
            rgb = np.dstack((r, g, b))
            
            # Normalisation pour l'affichage
            if stretch:
                # Éliminer les valeurs extrêmes (2-98 percentile)
                valid_pixels = rgb[rgb > 0]
                if len(valid_pixels) > 0:
                    p2, p98 = np.percentile(valid_pixels, (2, 98))
                    rgb = np.clip((rgb - p2) / (p98 - p2), 0, 1)
                else:
                    rgb = rgb / np.max(rgb) if np.max(rgb) > 0 else rgb
            else:
                # Mise à l'échelle simple
                rgb = rgb / np.max(rgb) if np.max(rgb) > 0 else rgb
            
            # Conversion en 8-bit [0,255]
            rgb_8bit = (rgb * 255).astype(np.uint8)
            
            # Création et sauvegarde de l'image
            img = Image.fromarray(rgb_8bit)
            img.save(output_path, format='PNG')
            return True
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde PNG: {e}")
        return False

def download_sentinel_image(coords, year, output_path, max_retries=3):
    """Télécharger une image Sentinel-2 pour des coordonnées données"""
    zone_size = 2240  # Taille en mètres (2240m x 2240m)
    
    for attempt in range(max_retries):
        try:
            # Création de la zone d'étude
            point = ee.Geometry.Point([coords[0], coords[1]])  # [lon, lat]
            roi = point.buffer(zone_size / 2).bounds()
            
            # Création de la composite Sentinel-2
            collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                .filterDate(f'{year}-01-01', f'{year}-12-31')
                .filterBounds(roi)
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 50))
                .map(mask_s2_clouds)
                .select(['B4', 'B3', 'B2'])  # Rouge, Vert, Bleu
            )
            
            composite = collection.median()
            
            # Paramètres de téléchargement
            params = {
                'region': roi,
                'dimensions': [224, 224],  # 224x224 pixels pour 2240m x 2240m le signe [] permet de forcer exactement la taille
                'format': 'GEO_TIFF',
                'crs': 'EPSG:4326'
            }
            
            # Télécharger le GeoTIFF en mémoire
            download_url = composite.getDownloadUrl(params)
            response = requests.get(download_url, timeout=120)
            response.raise_for_status()
            
            tiff_data = BytesIO(response.content)
            
            # Convertir et sauvegarder en PNG
            success = save_as_png(tiff_data, output_path)
            
            if success:
                return True
            else:
                if attempt < max_retries - 1:
                    print(f" Tentative {attempt + 1} échouée, nouvelle tentative dans 60s...")
                    time.sleep(60)
                continue
                
        except Exception as e:
            print(f" Erreur tentative {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                print(" Attente de 60 secondes avant nouvelle tentative...")
                time.sleep(60)
            else:
                print(f" Échec après {max_retries} tentatives")
                return False
    
    return False

def main():
    """Fonction principale du script"""
    
    # Paramètres configurables
    year = 2019  # Année des images à télécharger
    csv_file_path = r'D:\wealth_predict_sentinel_v2\data\output\processed_csv\points_avec_tuiles_EHCVM_2018.csv'
    base_output_dir = r'D:\wealth_predict_sentinel_v2\data\downloaded'
    
    # Nom du dossier de sortie (dynamique selon l'année)
    output_folder_name = f'Image_satellite_base_EHCVM_2018_Zoom_14_Sentinel_2_pour_an_{year}'
    output_dir = os.path.join(base_output_dir, output_folder_name)
    
    print(f"🚀 Début du téléchargement des images Sentinel-2 pour l'année {year}")
    print(f"📁 Dossier de sortie: {output_dir}")
    
    # Créer le dossier de sortie s'il n'existe pas
    os.makedirs(output_dir, exist_ok=True)
    print(f"✅ Dossier de sortie créé/vérifié")
    
    # Authentification GEE
    if not authenticate_and_initialize():
        return
    
    # Lecture du fichier CSV
    try:
        print(f"📖 Lecture du fichier CSV: {csv_file_path}")
        df = pd.read_csv(csv_file_path)
        print(f"✅ Fichier CSV lu avec succès ({len(df)} lignes)")
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du CSV: {e}")
        return
    
    # Vérifier que les colonnes nécessaires existent
    required_columns = ['tuile', 'tuile_center_lon', 'tuile_center_lat']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"❌ Colonnes manquantes dans le CSV: {missing_columns}")
        return
    
    # Identifier les tuiles uniques
    unique_tuiles = df[['tuile', 'tuile_center_lon', 'tuile_center_lat']].drop_duplicates()
    total_tuiles = len(unique_tuiles)
    print(f"🎯 {total_tuiles} tuiles uniques identifiées")
    
    # Statistiques de téléchargement
    downloaded_count = 0
    skipped_count = 0
    failed_count = 0
    
    # Barre de progression
    progress_bar = tqdm(
        unique_tuiles.iterrows(), 
        total=total_tuiles, 
        desc="Téléchargement en cours",
        unit="tuile"
    )
    
    for index, row in progress_bar:
        tuile = row['tuile']
        lon = row['tuile_center_lon']
        lat = row['tuile_center_lat']
        
        # Nom du fichier de sortie
        filename = f"{tuile}_{lon}_{lat}.png"
        output_path = os.path.join(output_dir, filename)
        
        # Vérifier si l'image existe déjà
        if os.path.exists(output_path):
            skipped_count += 1
            progress_bar.set_postfix({
                'Téléchargées': downloaded_count,
                'Ignorées': skipped_count,
                'Échecs': failed_count,
                'Actuelle': f"Tuile {tuile} (existante)"
            })
            continue
        
        # Mise à jour de la barre de progression
        progress_bar.set_postfix({
            'Téléchargées': downloaded_count,
            'Ignorées': skipped_count,
            'Échecs': failed_count,
            'Actuelle': f"Tuile {tuile}"
        })
        
        # Télécharger l'image
        coords = (lon, lat)  # (longitude, latitude)
        success = download_sentinel_image(coords, year, output_path)
        
        if success:
            downloaded_count += 1
        else:
            failed_count += 1
            print(f"\n❌ Échec du téléchargement: {filename}")
    
    # Résumé final
    print(f"\n" + "="*60)
    print(f"📊 RÉSUMÉ DU TÉLÉCHARGEMENT")
    print(f"="*60)
    print(f"🎯 Total de tuiles uniques: {total_tuiles}")
    print(f"✅ Images téléchargées: {downloaded_count}")
    print(f"⏭️ Images déjà existantes: {skipped_count}")
    print(f"❌ Échecs de téléchargement: {failed_count}")
    print(f"📁 Dossier de sortie: {output_dir}")
    print(f"="*60)
    
    if failed_count > 0:
        print(f"⚠️ {failed_count} téléchargements ont échoué. Vous pouvez relancer le script pour réessayer.")
    
    if downloaded_count > 0:
        print(f"🎉 Téléchargement terminé avec succès!")

if __name__ == "__main__":
    main()


# Sentinel-2 pour l'année 2021 - 50 % couverture nuageuse

# Script de téléchargement automatique d'images Sentinel-2 pour les tuiles EHCVM


def authenticate_and_initialize():
    """Authentification et initialisation de Google Earth Engine"""
    try:
        ee.Authenticate()
        ee.Initialize(project='') #enrez le nom du projet earth engine
        print("✅ Authentification GEE réussie")
        return True
    except Exception as e:
        print(f"❌ Erreur d'authentification GEE: {e}")
        return False

def mask_s2_clouds(image):
    """Fonction de masquage des nuages/ombres pour Sentinel-2"""
    qa = image.select('QA60')
    cloud_mask = 1 << 10
    shadow_mask = 1 << 11
    mask = qa.bitwiseAnd(cloud_mask).eq(0).And(qa.bitwiseAnd(shadow_mask).eq(0))
    return image.updateMask(mask)

def save_as_png(data, output_path, stretch=True):
    """Fonction de conversion et sauvegarde en PNG"""
    try:
        with rasterio.open(data) as src:
            # Lire les bandes (ordre: R, G, B)
            r = src.read(1)
            g = src.read(2)
            b = src.read(3)
            
            # Combiner en image RGB
            rgb = np.dstack((r, g, b))
            
            # Normalisation pour l'affichage
            if stretch:
                # Éliminer les valeurs extrêmes (2-98 percentile)
                valid_pixels = rgb[rgb > 0]
                if len(valid_pixels) > 0:
                    p2, p98 = np.percentile(valid_pixels, (2, 98))
                    rgb = np.clip((rgb - p2) / (p98 - p2), 0, 1)
                else:
                    rgb = rgb / np.max(rgb) if np.max(rgb) > 0 else rgb
            else:
                # Mise à l'échelle simple
                rgb = rgb / np.max(rgb) if np.max(rgb) > 0 else rgb
            
            # Conversion en 8-bit [0,255]
            rgb_8bit = (rgb * 255).astype(np.uint8)
            
            # Création et sauvegarde de l'image
            img = Image.fromarray(rgb_8bit)
            img.save(output_path, format='PNG')
            return True
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde PNG: {e}")
        return False

def download_sentinel_image(coords, year, output_path, max_retries=3):
    """Télécharger une image Sentinel-2 pour des coordonnées données"""
    zone_size = 2240  # Taille en mètres (2240m x 2240m)
    
    for attempt in range(max_retries):
        try:
            # Création de la zone d'étude
            point = ee.Geometry.Point([coords[0], coords[1]])  # [lon, lat]
            roi = point.buffer(zone_size / 2).bounds()
            
            # Création de la composite Sentinel-2
            collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                .filterDate(f'{year}-01-01', f'{year}-12-31')
                .filterBounds(roi)
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 50))
                .map(mask_s2_clouds)
                .select(['B4', 'B3', 'B2'])  # Rouge, Vert, Bleu
            )
            
            composite = collection.median()
            
            # Paramètres de téléchargement
            params = {
                'region': roi,
                'dimensions': [224, 224],  # 224x224 pixels pour 2240m x 2240m
                'format': 'GEO_TIFF',
                'crs': 'EPSG:4326'
            }
            
            # Télécharger le GeoTIFF en mémoire
            download_url = composite.getDownloadUrl(params)
            response = requests.get(download_url, timeout=120)
            response.raise_for_status()
            
            tiff_data = BytesIO(response.content)
            
            # Convertir et sauvegarder en PNG
            success = save_as_png(tiff_data, output_path)
            
            if success:
                return True
            else:
                if attempt < max_retries - 1:
                    print(f"⚠️ Tentative {attempt + 1} échouée, nouvelle tentative dans 60s...")
                    time.sleep(60)
                continue
                
        except Exception as e:
            print(f"⚠️ Erreur tentative {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                print("⏳ Attente de 60 secondes avant nouvelle tentative...")
                time.sleep(60)
            else:
                print(f"❌ Échec après {max_retries} tentatives")
                return False
    
    return False

def main():
    """Fonction principale du script"""
    
    # Paramètres configurables
    year = 2021  # Année des images à télécharger
    csv_file_path = r'D:\wealth_predict_sentinel_v2\data\output\processed_csv\points_avec_tuiles_EHCVM_2018.csv'
    base_output_dir = r'D:\wealth_predict_sentinel_v2\data\downloaded'
    
    # Nom du dossier de sortie (dynamique selon l'année)
    output_folder_name = f'Image_satellite_base_EHCVM_2018_Zoom_14_Sentinel_2_pour_an_{year}'
    output_dir = os.path.join(base_output_dir, output_folder_name)
    
    print(f"🚀 Début du téléchargement des images Sentinel-2 pour l'année {year}")
    print(f"📁 Dossier de sortie: {output_dir}")
    
    # Créer le dossier de sortie s'il n'existe pas
    os.makedirs(output_dir, exist_ok=True)
    print(f"✅ Dossier de sortie créé/vérifié")
    
    # Authentification GEE
    if not authenticate_and_initialize():
        return
    
    # Lecture du fichier CSV
    try:
        print(f"📖 Lecture du fichier CSV: {csv_file_path}")
        df = pd.read_csv(csv_file_path)
        print(f"✅ Fichier CSV lu avec succès ({len(df)} lignes)")
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du CSV: {e}")
        return
    
    # Vérifier que les colonnes nécessaires existent
    required_columns = ['tuile', 'tuile_center_lon', 'tuile_center_lat']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"❌ Colonnes manquantes dans le CSV: {missing_columns}")
        return
    
    # Identifier les tuiles uniques
    unique_tuiles = df[['tuile', 'tuile_center_lon', 'tuile_center_lat']].drop_duplicates()
    total_tuiles = len(unique_tuiles)
    print(f"🎯 {total_tuiles} tuiles uniques identifiées")
    
    # Statistiques de téléchargement
    downloaded_count = 0
    skipped_count = 0
    failed_count = 0
    
    # Barre de progression
    progress_bar = tqdm(
        unique_tuiles.iterrows(), 
        total=total_tuiles, 
        desc="Téléchargement en cours",
        unit="tuile"
    )
    
    for index, row in progress_bar:
        tuile = row['tuile']
        lon = row['tuile_center_lon']
        lat = row['tuile_center_lat']
        
        # Nom du fichier de sortie
        filename = f"{tuile}_{lon}_{lat}.png"
        output_path = os.path.join(output_dir, filename)
        
        # Vérifier si l'image existe déjà
        if os.path.exists(output_path):
            skipped_count += 1
            progress_bar.set_postfix({
                'Téléchargées': downloaded_count,
                'Ignorées': skipped_count,
                'Échecs': failed_count,
                'Actuelle': f"Tuile {tuile} (existante)"
            })
            continue
        
        # Mise à jour de la barre de progression
        progress_bar.set_postfix({
            'Téléchargées': downloaded_count,
            'Ignorées': skipped_count,
            'Échecs': failed_count,
            'Actuelle': f"Tuile {tuile}"
        })
        
        # Télécharger l'image
        coords = (lon, lat)  # (longitude, latitude)
        success = download_sentinel_image(coords, year, output_path)
        
        if success:
            downloaded_count += 1
        else:
            failed_count += 1
            print(f"\n❌ Échec du téléchargement: {filename}")
    
    # Résumé final
    print(f"\n" + "="*60)
    print(f"📊 RÉSUMÉ DU TÉLÉCHARGEMENT")
    print(f"="*60)
    print(f"🎯 Total de tuiles uniques: {total_tuiles}")
    print(f"✅ Images téléchargées: {downloaded_count}")
    print(f"⏭️ Images déjà existantes: {skipped_count}")
    print(f"❌ Échecs de téléchargement: {failed_count}")
    print(f"📁 Dossier de sortie: {output_dir}")
    print(f"="*60)
    
    if failed_count > 0:
        print(f"⚠️ {failed_count} téléchargements ont échoué. Vous pouvez relancer le script pour réessayer.")
    
    if downloaded_count > 0:
        print(f"🎉 Téléchargement terminé avec succès!")

if __name__ == "__main__":
    main()


# Sentinel-2 pour l'année 2023 - 50 % couverture nuageuse

# Script de téléchargement automatique d'images Sentinel-2 pour les tuiles EHCVM

def authenticate_and_initialize():
    """Authentification et initialisation de Google Earth Engine"""
    try:
        ee.Authenticate()
        ee.Initialize(project='')
        print("✅ Authentification GEE réussie")
        return True
    except Exception as e:
        print(f"❌ Erreur d'authentification GEE: {e}")
        return False

def mask_s2_clouds(image):
    """Fonction de masquage des nuages/ombres pour Sentinel-2"""
    qa = image.select('QA60')
    cloud_mask = 1 << 10
    shadow_mask = 1 << 11
    mask = qa.bitwiseAnd(cloud_mask).eq(0).And(qa.bitwiseAnd(shadow_mask).eq(0))
    return image.updateMask(mask)

def save_as_png(data, output_path, stretch=True):
    """Fonction de conversion et sauvegarde en PNG"""
    try:
        with rasterio.open(data) as src:
            # Lire les bandes (ordre: R, G, B)
            r = src.read(1)
            g = src.read(2)
            b = src.read(3)
            
            # Combiner en image RGB
            rgb = np.dstack((r, g, b))
            
            # Normalisation pour l'affichage
            if stretch:
                # Éliminer les valeurs extrêmes (2-98 percentile)
                valid_pixels = rgb[rgb > 0]
                if len(valid_pixels) > 0:
                    p2, p98 = np.percentile(valid_pixels, (2, 98))
                    rgb = np.clip((rgb - p2) / (p98 - p2), 0, 1)
                else:
                    rgb = rgb / np.max(rgb) if np.max(rgb) > 0 else rgb
            else:
                # Mise à l'échelle simple
                rgb = rgb / np.max(rgb) if np.max(rgb) > 0 else rgb
            
            # Conversion en 8-bit [0,255]
            rgb_8bit = (rgb * 255).astype(np.uint8)
            
            # Création et sauvegarde de l'image
            img = Image.fromarray(rgb_8bit)
            img.save(output_path, format='PNG')
            return True
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde PNG: {e}")
        return False

def download_sentinel_image(coords, year, output_path, max_retries=3):
    """Télécharger une image Sentinel-2 pour des coordonnées données"""
    zone_size = 2240  # Taille en mètres (2240m x 2240m)
    
    for attempt in range(max_retries):
        try:
            # Création de la zone d'étude
            point = ee.Geometry.Point([coords[0], coords[1]])  # [lon, lat]
            roi = point.buffer(zone_size / 2).bounds()
            
            # Création de la composite Sentinel-2
            collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                .filterDate(f'{year}-01-01', f'{year}-12-31')
                .filterBounds(roi)
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 50))
                .map(mask_s2_clouds)
                .select(['B4', 'B3', 'B2'])  # Rouge, Vert, Bleu
            )
            
            composite = collection.median()
            
            # Paramètres de téléchargement
            params = {
                'region': roi,
                'dimensions': [224, 224],  # 224x224 pixels pour 2240m x 2240m
                'format': 'GEO_TIFF',
                'crs': 'EPSG:4326'
            }
            
            # Télécharger le GeoTIFF en mémoire
            download_url = composite.getDownloadUrl(params)
            response = requests.get(download_url, timeout=120)
            response.raise_for_status()
            
            tiff_data = BytesIO(response.content)
            
            # Convertir et sauvegarder en PNG
            success = save_as_png(tiff_data, output_path)
            
            if success:
                return True
            else:
                if attempt < max_retries - 1:
                    print(f"⚠️ Tentative {attempt + 1} échouée, nouvelle tentative dans 60s...")
                    time.sleep(60)
                continue
                
        except Exception as e:
            print(f"⚠️ Erreur tentative {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                print("⏳ Attente de 60 secondes avant nouvelle tentative...")
                time.sleep(60)
            else:
                print(f"❌ Échec après {max_retries} tentatives")
                return False
    
    return False

def main():
    """Fonction principale du script"""
    
    # Paramètres configurables
    year = 2023  # Année des images à télécharger
    csv_file_path = r'D:\wealth_predict_sentinel_v2\data\output\processed_csv\points_avec_tuiles_EHCVM_2018.csv'
    base_output_dir = r'D:\wealth_predict_sentinel_v2\data\downloaded'
    
    # Nom du dossier de sortie (dynamique selon l'année)
    output_folder_name = f'Image_satellite_base_EHCVM_2018_Zoom_14_Sentinel_2_pour_an_{year}'
    output_dir = os.path.join(base_output_dir, output_folder_name)
    
    print(f"🚀 Début du téléchargement des images Sentinel-2 pour l'année {year}")
    print(f"📁 Dossier de sortie: {output_dir}")
    
    # Créer le dossier de sortie s'il n'existe pas
    os.makedirs(output_dir, exist_ok=True)
    print(f"✅ Dossier de sortie créé/vérifié")
    
    # Authentification GEE
    if not authenticate_and_initialize():
        return
    
    # Lecture du fichier CSV
    try:
        print(f"📖 Lecture du fichier CSV: {csv_file_path}")
        df = pd.read_csv(csv_file_path)
        print(f"✅ Fichier CSV lu avec succès ({len(df)} lignes)")
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du CSV: {e}")
        return
    
    # Vérifier que les colonnes nécessaires existent
    required_columns = ['tuile', 'tuile_center_lon', 'tuile_center_lat']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"❌ Colonnes manquantes dans le CSV: {missing_columns}")
        return
    
    # Identifier les tuiles uniques
    unique_tuiles = df[['tuile', 'tuile_center_lon', 'tuile_center_lat']].drop_duplicates()
    total_tuiles = len(unique_tuiles)
    print(f"🎯 {total_tuiles} tuiles uniques identifiées")
    
    # Statistiques de téléchargement
    downloaded_count = 0
    skipped_count = 0
    failed_count = 0
    
    # Barre de progression
    progress_bar = tqdm(
        unique_tuiles.iterrows(), 
        total=total_tuiles, 
        desc="Téléchargement en cours",
        unit="tuile"
    )
    
    for index, row in progress_bar:
        tuile = row['tuile']
        lon = row['tuile_center_lon']
        lat = row['tuile_center_lat']
        
        # Nom du fichier de sortie
        filename = f"{tuile}_{lon}_{lat}.png"
        output_path = os.path.join(output_dir, filename)
        
        # Vérifier si l'image existe déjà
        if os.path.exists(output_path):
            skipped_count += 1
            progress_bar.set_postfix({
                'Téléchargées': downloaded_count,
                'Ignorées': skipped_count,
                'Échecs': failed_count,
                'Actuelle': f"Tuile {tuile} (existante)"
            })
            continue
        
        # Mise à jour de la barre de progression
        progress_bar.set_postfix({
            'Téléchargées': downloaded_count,
            'Ignorées': skipped_count,
            'Échecs': failed_count,
            'Actuelle': f"Tuile {tuile}"
        })
        
        # Télécharger l'image
        coords = (lon, lat)  # (longitude, latitude)
        success = download_sentinel_image(coords, year, output_path)
        
        if success:
            downloaded_count += 1
        else:
            failed_count += 1
            print(f"\n❌ Échec du téléchargement: {filename}")
    
    # Résumé final
    print(f"\n" + "="*60)
    print(f"📊 RÉSUMÉ DU TÉLÉCHARGEMENT")
    print(f"="*60)
    print(f"🎯 Total de tuiles uniques: {total_tuiles}")
    print(f"✅ Images téléchargées: {downloaded_count}")
    print(f"⏭️ Images déjà existantes: {skipped_count}")
    print(f"❌ Échecs de téléchargement: {failed_count}")
    print(f"📁 Dossier de sortie: {output_dir}")
    print(f"="*60)
    
    if failed_count > 0:
        print(f"⚠️ {failed_count} téléchargements ont échoué. Vous pouvez relancer le script pour réessayer.")
    
    if downloaded_count > 0:
        print(f"🎉 Téléchargement terminé avec succès!")

if __name__ == "__main__":
    main()


# Sentinel-2 pour l'année 2024 - 50 % couverture nuageuse


# Script de téléchargement automatique d'images Sentinel-2 pour les tuiles EHCVM


def authenticate_and_initialize():
    """Authentification et initialisation de Google Earth Engine"""
    try:
        ee.Authenticate()
        ee.Initialize(project='')
        print("✅ Authentification GEE réussie")
        return True
    except Exception as e:
        print(f"❌ Erreur d'authentification GEE: {e}")
        return False

def mask_s2_clouds(image):
    """Fonction de masquage des nuages/ombres pour Sentinel-2"""
    qa = image.select('QA60')
    cloud_mask = 1 << 10
    shadow_mask = 1 << 11
    mask = qa.bitwiseAnd(cloud_mask).eq(0).And(qa.bitwiseAnd(shadow_mask).eq(0))
    return image.updateMask(mask)

def save_as_png(data, output_path, stretch=True):
    """Fonction de conversion et sauvegarde en PNG"""
    try:
        with rasterio.open(data) as src:
            # Lire les bandes (ordre: R, G, B)
            r = src.read(1)
            g = src.read(2)
            b = src.read(3)
            
            # Combiner en image RGB
            rgb = np.dstack((r, g, b))
            
            # Normalisation pour l'affichage
            if stretch:
                # Éliminer les valeurs extrêmes (2-98 percentile)
                valid_pixels = rgb[rgb > 0]
                if len(valid_pixels) > 0:
                    p2, p98 = np.percentile(valid_pixels, (2, 98))
                    rgb = np.clip((rgb - p2) / (p98 - p2), 0, 1)
                else:
                    rgb = rgb / np.max(rgb) if np.max(rgb) > 0 else rgb
            else:
                # Mise à l'échelle simple
                rgb = rgb / np.max(rgb) if np.max(rgb) > 0 else rgb
            
            # Conversion en 8-bit [0,255]
            rgb_8bit = (rgb * 255).astype(np.uint8)
            
            # Création et sauvegarde de l'image
            img = Image.fromarray(rgb_8bit)
            img.save(output_path, format='PNG')
            return True
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde PNG: {e}")
        return False

def download_sentinel_image(coords, year, output_path, max_retries=3):
    """Télécharger une image Sentinel-2 pour des coordonnées données"""
    zone_size = 2240  # Taille en mètres (2240m x 2240m)
    
    for attempt in range(max_retries):
        try:
            # Création de la zone d'étude
            point = ee.Geometry.Point([coords[0], coords[1]])  # [lon, lat]
            roi = point.buffer(zone_size / 2).bounds()
            
            # Création de la composite Sentinel-2
            collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                .filterDate(f'{year}-01-01', f'{year}-12-31')
                .filterBounds(roi)
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 50))
                .map(mask_s2_clouds)
                .select(['B4', 'B3', 'B2'])  # Rouge, Vert, Bleu
            )
            
            composite = collection.median()
            
            # Paramètres de téléchargement
            params = {
                'region': roi,
                'dimensions': [224, 224],  # 224x224 pixels pour 2240m x 2240m
                'format': 'GEO_TIFF',
                'crs': 'EPSG:4326'
            }
            
            # Télécharger le GeoTIFF en mémoire
            download_url = composite.getDownloadUrl(params)
            response = requests.get(download_url, timeout=120)
            response.raise_for_status()
            
            tiff_data = BytesIO(response.content)
            
            # Convertir et sauvegarder en PNG
            success = save_as_png(tiff_data, output_path)
            
            if success:
                return True
            else:
                if attempt < max_retries - 1:
                    print(f"⚠️ Tentative {attempt + 1} échouée, nouvelle tentative dans 60s...")
                    time.sleep(60)
                continue
                
        except Exception as e:
            print(f"⚠️ Erreur tentative {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                print("⏳ Attente de 60 secondes avant nouvelle tentative...")
                time.sleep(60)
            else:
                print(f"❌ Échec après {max_retries} tentatives")
                return False
    
    return False

def main():
    """Fonction principale du script"""
    
    # Paramètres configurables
    year = 2023  # Année des images à télécharger
    csv_file_path = r'D:\wealth_predict_sentinel_v2\data\output\processed_csv\points_avec_tuiles_EHCVM_2018.csv'
    base_output_dir = r'D:\wealth_predict_sentinel_v2\data\downloaded'
    
    # Nom du dossier de sortie (dynamique selon l'année)
    output_folder_name = f'Image_satellite_base_EHCVM_2018_Zoom_14_Sentinel_2_pour_an_{year}'
    output_dir = os.path.join(base_output_dir, output_folder_name)
    
    print(f"🚀 Début du téléchargement des images Sentinel-2 pour l'année {year}")
    print(f"📁 Dossier de sortie: {output_dir}")
    
    # Créer le dossier de sortie s'il n'existe pas
    os.makedirs(output_dir, exist_ok=True)
    print(f"✅ Dossier de sortie créé/vérifié")
    
    # Authentification GEE
    if not authenticate_and_initialize():
        return
    
    # Lecture du fichier CSV
    try:
        print(f"📖 Lecture du fichier CSV: {csv_file_path}")
        df = pd.read_csv(csv_file_path)
        print(f"✅ Fichier CSV lu avec succès ({len(df)} lignes)")
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du CSV: {e}")
        return
    
    # Vérifier que les colonnes nécessaires existent
    required_columns = ['tuile', 'tuile_center_lon', 'tuile_center_lat']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"❌ Colonnes manquantes dans le CSV: {missing_columns}")
        return
    
    # Identifier les tuiles uniques
    unique_tuiles = df[['tuile', 'tuile_center_lon', 'tuile_center_lat']].drop_duplicates()
    total_tuiles = len(unique_tuiles)
    print(f"🎯 {total_tuiles} tuiles uniques identifiées")
    
    # Statistiques de téléchargement
    downloaded_count = 0
    skipped_count = 0
    failed_count = 0
    
    # Barre de progression
    progress_bar = tqdm(
        unique_tuiles.iterrows(), 
        total=total_tuiles, 
        desc="Téléchargement en cours",
        unit="tuile"
    )
    
    for index, row in progress_bar:
        tuile = row['tuile']
        lon = row['tuile_center_lon']
        lat = row['tuile_center_lat']
        
        # Nom du fichier de sortie
        filename = f"{tuile}_{lon}_{lat}.png"
        output_path = os.path.join(output_dir, filename)
        
        # Vérifier si l'image existe déjà
        if os.path.exists(output_path):
            skipped_count += 1
            progress_bar.set_postfix({
                'Téléchargées': downloaded_count,
                'Ignorées': skipped_count,
                'Échecs': failed_count,
                'Actuelle': f"Tuile {tuile} (existante)"
            })
            continue
        
        # Mise à jour de la barre de progression
        progress_bar.set_postfix({
            'Téléchargées': downloaded_count,
            'Ignorées': skipped_count,
            'Échecs': failed_count,
            'Actuelle': f"Tuile {tuile}"
        })
        
        # Télécharger l'image
        coords = (lon, lat)  # (longitude, latitude)
        success = download_sentinel_image(coords, year, output_path)
        
        if success:
            downloaded_count += 1
        else:
            failed_count += 1
            print(f"\n❌ Échec du téléchargement: {filename}")
    
    # Résumé final
    print(f"\n" + "="*60)
    print(f"📊 RÉSUMÉ DU TÉLÉCHARGEMENT")
    print(f"="*60)
    print(f"🎯 Total de tuiles uniques: {total_tuiles}")
    print(f"✅ Images téléchargées: {downloaded_count}")
    print(f"⏭️ Images déjà existantes: {skipped_count}")
    print(f"❌ Échecs de téléchargement: {failed_count}")
    print(f"📁 Dossier de sortie: {output_dir}")
    print(f"="*60)
    
    if failed_count > 0:
        print(f"⚠️ {failed_count} téléchargements ont échoué. Vous pouvez relancer le script pour réessayer.")
    
    if downloaded_count > 0:
        print(f"🎉 Téléchargement terminé avec succès!")

if __name__ == "__main__":
    main()
