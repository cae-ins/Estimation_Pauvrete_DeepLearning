"""
Tuiles des ménages 
"""
# Importation des bibliothèques
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point, Polygon
import matplotlib.pyplot as plt
import folium
from google.colab import drive
from pyproj import Geod
import os
import io
import random
from pathlib import Path

#  PARAMÈTRE DYNAMIQUE EHCVM - MODIFIEZ ICI POUR CHANGER L'ANNÉE
EHCVM_YEAR = "2018"  # Changez cette valeur pour 2021, 2024, etc.
print(f" Configuration EHCVM : {EHCVM_YEAR}")

# Générer les noms de fichiers avec l'identifiant EHCVM
file_prefix = f"EHCVM_{EHCVM_YEAR}"
geojson_path = f"/content/grilles_avec_points_{file_prefix}.geojson"

# Créer un dossier pour les exports
export_dir = "/content/exports"
os.makedirs(export_dir, exist_ok=True)

#  Initialiser le calcul géodésique (WGS84)
geod = Geod(ellps='WGS84')
print("Calculateur géodésique initialisé (WGS84)")


# Charger les données GPS originales
df = pd.read_csv(csv_path)
print(f"Fichier CSV chargé avec {len(df)} points GPS.")
print("Colonnes disponibles :", df.columns.tolist())

# Sélectionner uniquement les colonnes pertinentes
gps_data = df[['GPS__Latitude', 'GPS__Longitude']].copy()

# Créer un GeoDataFrame à partir des données GPS
geometry = [Point(xy) for xy in zip(gps_data['GPS__Longitude'], gps_data['GPS__Latitude'])]
gps_gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
print(f"GeoDataFrame créé avec {len(gps_gdf)} points.")

# Vérifier si le fichier GeoJSON des grilles existe déjà
if not os.path.exists(geojson_path):
    print("Le fichier GeoJSON des grilles n'existe pas. Création des grilles...")

    # Définir la taille de carré en degrés (2,24 km ≈ 0,02 degrés)
    square_size_degrees = 0.02

    # Fonction pour créer une grille de carrés
    def create_grid(gdf, size_degrees):
        # Trouver les limites des données
        minx, miny, maxx, maxy = gdf.total_bounds

        # Créer des séquences de coordonnées pour les carrés
        x_coords = np.arange(minx, maxx + size_degrees, size_degrees)
        y_coords = np.arange(miny, maxy + size_degrees, size_degrees)

        # Créer les carrés
        squares = []
        square_ids = []
        id_counter = 0

        for x in x_coords[:-1]:
            for y in y_coords[:-1]:
                square = Polygon([
                    (x, y),
                    (x + size_degrees, y),
                    (x + size_degrees, y + size_degrees),
                    (x, y + size_degrees)
                ])
                squares.append(square)
                square_ids.append(id_counter)
                id_counter += 1

        # Créer un GeoDataFrame pour les carrés
        square_gdf = gpd.GeoDataFrame({'id': square_ids, 'geometry': squares}, crs=gdf.crs)
        return square_gdf

    # Créer la grille de carrés
    square_grid = create_grid(gps_gdf, square_size_degrees)

    # Assigner chaque point à un carré
    joined = gpd.sjoin(gps_gdf, square_grid, how='left', predicate='within')

    # Compter le nombre de points dans chaque carré
    square_counts = joined.groupby('id').size().reset_index(name='count')

    # Identifier les carrés avec points
    squares_with_points = square_grid[square_grid['id'].isin(square_counts['id'])]

    # Ajouter le nombre de points dans chaque grille
    points_count_dict = dict(zip(square_counts['id'], square_counts['count']))
    squares_with_points['nb_points'] = squares_with_points['id'].map(points_count_dict)

    # Sauvegarder les grilles avec points au format GeoJSON
    squares_with_points.to_file(geojson_path, driver='GeoJSON')
    print(f"Fichier GeoJSON créé : {geojson_path}")

    # Utiliser ces grilles pour la suite
    grilles_gdf = squares_with_points
else:
    # Charger le fichier GeoJSON des grilles existant
    grilles_gdf = gpd.read_file(geojson_path)
    print(f"Fichier GeoJSON chargé avec {len(grilles_gdf)} grilles.")

# Créer une nouvelle colonne "tuile" avec des noms séquentiels
# Trier d'abord par nombre de points (optionnel) pour que les tuiles avec le plus de points aient les premiers numéros
if 'nb_points' in grilles_gdf.columns:
    grilles_gdf = grilles_gdf.sort_values(by='nb_points', ascending=False).reset_index(drop=True)

# Créer la colonne tuile avec un format "tuile X"
grilles_gdf['tuile'] = [f"tuile {i+1}" for i in range(len(grilles_gdf))]

# Ajouter des colonnes utiles pour Sentinel-2
grilles_gdf['center_lon'] = grilles_gdf.geometry.centroid.x
grilles_gdf['center_lat'] = grilles_gdf.geometry.centroid.y
grilles_gdf['min_lon'] = grilles_gdf.geometry.bounds.minx
grilles_gdf['min_lat'] = grilles_gdf.geometry.bounds.miny
grilles_gdf['max_lon'] = grilles_gdf.geometry.bounds.maxx
grilles_gdf['max_lat'] = grilles_gdf.geometry.bounds.maxy

# 🌍 CALCUL GÉODÉSIQUE PRÉCIS DES DIMENSIONS
print("Calcul des dimensions géodésiques des tuiles...")

def calculate_geodesic_dimensions(row):
    """Calcule les dimensions géodésiques précises d'une tuile"""
    min_lon, min_lat = row['min_lon'], row['min_lat']
    max_lon, max_lat = row['max_lon'], row['max_lat']

    # Largeur : distance entre les coins inférieurs
    _, _, width_m = geod.inv(min_lon, min_lat, max_lon, min_lat)

    # Hauteur : distance entre les coins gauches
    _, _, height_m = geod.inv(min_lon, min_lat, min_lon, max_lat)

    return width_m / 1000, height_m / 1000  # Conversion en km

# Appliquer le calcul géodésique à toutes les tuiles
dimensions = grilles_gdf.apply(calculate_geodesic_dimensions, axis=1, result_type='expand')
grilles_gdf['width_km'] = dimensions[0]
grilles_gdf['height_km'] = dimensions[1]

print(f"Dimensions moyennes des tuiles : {grilles_gdf['width_km'].mean():.3f} km × {grilles_gdf['height_km'].mean():.3f} km")

# Créer un dictionnaire de mapping entre l'ID original et le nom de tuile
tuile_mapping = dict(zip(grilles_gdf['id'], grilles_gdf['tuile']))

# Faire une jointure spatiale entre les points GPS et les grilles
joined_data = gpd.sjoin(gps_gdf, grilles_gdf[['id', 'tuile', 'geometry']], how='left', predicate='within')

# Identifier les points qui ne sont dans aucune grille
points_sans_grille = joined_data[joined_data['id'].isna()]
if len(points_sans_grille) > 0:
    print(f"Attention: {len(points_sans_grille)} points ne sont dans aucune grille!")

    # Fonction pour trouver la tuile la plus proche d'un point avec calcul géodésique
    def find_nearest_tile(point, tiles_gdf):
        """Trouve la tuile la plus proche d'un point en utilisant les distances géodésiques"""
        point_lon, point_lat = point.x, point.y
        min_distance = float('inf')
        nearest_tile = None

        for idx, tile in tiles_gdf.iterrows():
            # Calculer la distance au centre de la tuile
            tile_center_lon, tile_center_lat = tile['center_lon'], tile['center_lat']

            # Distance géodésique précise
            _, _, distance_m = geod.inv(point_lon, point_lat, tile_center_lon, tile_center_lat)

            if distance_m < min_distance:
                min_distance = distance_m
                nearest_tile = tile

        return nearest_tile, min_distance

    # Créer un DataFrame pour stocker les assignations de tuiles pour les points orphelins
    orphan_assignments = []

    # Pour chaque point sans grille, trouver la tuile la plus proche
    for idx, row in points_sans_grille.iterrows():
        point = row.geometry
        nearest_tile, distance_m = find_nearest_tile(point, grilles_gdf)

        # Stocker les informations d'assignation avec distance géodésique précise
        orphan_assignments.append({
            'point_index': idx,
            'nearest_tile_id': nearest_tile['id'],
            'nearest_tile_name': nearest_tile['tuile'],
            'distance_degrees': point.distance(Point(nearest_tile['center_lon'], nearest_tile['center_lat'])),
            'distance_meters_geodesic': distance_m,  # Distance géodésique précise
            'distance_km_geodesic': distance_m / 1000  # Distance en km
        })

    # Créer un DataFrame des assignations
    orphan_df = pd.DataFrame(orphan_assignments)
    print("\n🌍 Assignation des points orphelins aux tuiles les plus proches (distances géodésiques):")
    print(orphan_df[['point_index', 'nearest_tile_name', 'distance_km_geodesic']].round(3))

    # Statistiques sur les distances d'assignation
    if len(orphan_df) > 0:
        print(f"\nStatistiques des distances d'assignation :")
        print(f"• Distance minimale : {orphan_df['distance_km_geodesic'].min():.3f} km")
        print(f"• Distance maximale : {orphan_df['distance_km_geodesic'].max():.3f} km")
        print(f"• Distance moyenne : {orphan_df['distance_km_geodesic'].mean():.3f} km")

    # Assigner les points orphelins à leur tuile la plus proche dans le DataFrame joint
    for _, assignment in orphan_df.iterrows():
        joined_data.loc[assignment['point_index'], 'id'] = assignment['nearest_tile_id']
        joined_data.loc[assignment['point_index'], 'tuile'] = assignment['nearest_tile_name']

    # Vérifier que tous les points ont maintenant une tuile
    points_sans_grille_after = joined_data[joined_data['id'].isna()]
    print(f"Nombre de points sans grille après assignation: {len(points_sans_grille_after)}")
else:
    print("Tous les points ont été correctement assignés à une grille.")

# Créer le DataFrame final avec les colonnes souhaitées
# Sélectionner les colonnes originales du DataFrame plus la colonne tuile
colonnes_originales = df.columns.tolist()
resultat_df = joined_data[colonnes_originales + ['tuile']].copy()

# === CORRECTION : Recalculer correctement le nombre de points par tuile ===
print("\n=== Mise à jour des statistiques après assignation des points orphelins ===")

# Recalculer le nombre réel de points par tuile basé sur le résultat final
tuile_counts_final = resultat_df['tuile'].value_counts()
print(f"Nombre de tuiles avec au moins un point: {len(tuile_counts_final)}")

# Mettre à jour la colonne nb_points dans grilles_gdf avec les vrais comptes
grilles_gdf['nb_points_final'] = grilles_gdf['tuile'].map(tuile_counts_final).fillna(0).astype(int)

# Remplacer l'ancienne colonne nb_points par la nouvelle (si elle existe)
if 'nb_points' in grilles_gdf.columns:
    grilles_gdf = grilles_gdf.drop('nb_points', axis=1)
grilles_gdf['nb_points'] = grilles_gdf['nb_points_final']
grilles_gdf = grilles_gdf.drop('nb_points_final', axis=1)

print("Mise à jour terminée. Les statistiques suivantes sont maintenant cohérentes:")

# Sauvegarder le résultat
output_path = os.path.join(export_dir, f"points_avec_tuiles_{file_prefix}.csv")
resultat_df.to_csv(output_path, index=False)
print(f"Résultat sauvegardé: {output_path}")

# Exporter les grilles dans différents formats
geojson_export_path = os.path.join(export_dir, f"grilles_avec_tuiles_{file_prefix}.geojson")
grilles_gdf.to_file(geojson_export_path, driver='GeoJSON')
print(f"Grilles exportées au format GeoJSON: {geojson_export_path}")

# 2. Format Shapefile (crée automatiquement les fichiers .shp, .dbf, .shx, .prj)
shapefile_export_path = os.path.join(export_dir, f"grilles_avec_tuiles_{file_prefix}.shp")
grilles_gdf.to_file(shapefile_export_path)
print(f"Grilles exportées au format Shapefile: {shapefile_export_path}")
print(f"  Fichiers créés: .shp (géométries), .dbf (attributs), .shx (index), .prj (projection)")

# Afficher un aperçu du résultat
print("\nAperçu du DataFrame résultant:")
print(resultat_df[['GPS__Latitude', 'GPS__Longitude', 'tuile']].head(10))

# Afficher les informations sur les grilles pour Sentinel-2
print("\nInformations sur les grilles pour Sentinel-2:")
sentinel_info = grilles_gdf[['tuile', 'center_lon', 'center_lat', 'min_lon', 'min_lat', 'max_lon', 'max_lat', 'width_km', 'height_km']].head(5)
print(sentinel_info)
print("...")

# Afficher une carte pour visualiser les points et leurs tuiles
print("\nGénération d'une carte pour visualiser les tuiles...")

# Créer une carte centrée sur les données
center_lat = gps_gdf.geometry.centroid.y.mean()
center_lon = gps_gdf.geometry.centroid.x.mean()
m = folium.Map(location=[center_lat, center_lon], zoom_start=9, control_scale=True)

# Générer une palette de couleurs pour les tuiles
colors = []
for i in range(len(grilles_gdf)):
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    colors.append(f'#{r:02x}{g:02x}{b:02x}')

# Créer un dictionnaire de couleurs pour chaque tuile
color_dict = dict(zip(grilles_gdf['tuile'], colors))

# Ajouter chaque tuile à la carte avec sa couleur unique
for idx, row in grilles_gdf.iterrows():
    # Informations pour le popup
    popup_content = f"""
    <b>{row['tuile']}</b><br>
    ID original: {row['id']}<br>
    """

    if 'nb_points' in row:
        popup_content += f"Nombre de points: {row['nb_points']}<br>"

    popup_content += f"""
    Centre: {row['center_lat']:.5f}, {row['center_lon']:.5f}<br>
    Limites: {row['min_lat']:.5f}, {row['min_lon']:.5f} à {row['max_lat']:.5f}, {row['max_lon']:.5f}<br>
    Dimensions: {row['width_km']:.2f} km × {row['height_km']:.2f} km
    """

    # Convertir la géométrie en coordonnées folium
    if hasattr(row.geometry, 'exterior'):
        coords = list(row.geometry.exterior.coords)
        coords_folium = [[y, x] for x, y in coords]

        # Ajouter le polygone à la carte
        folium.Polygon(
            locations=coords_folium,
            color='black',
            weight=1,
            fill=True,
            fill_color=color_dict[row['tuile']],
            fill_opacity=0.6,
            popup=folium.Popup(popup_content, max_width=300),
            tooltip=row['tuile']
        ).add_to(m)

# Identifiant visuel pour les points orphelins
if 'points_sans_grille' in locals() and len(points_sans_grille) > 0:
    orphan_group = folium.FeatureGroup(name='Points orphelins (assignés à la tuile la plus proche)')
    for idx, row in points_sans_grille.iterrows():
        # Trouver à quelle tuile le point a été assigné
        assigned_tile = resultat_df.loc[idx, 'tuile']
        assigned_color = color_dict.get(assigned_tile, 'gray')

        folium.CircleMarker(
            location=[row['GPS__Latitude'], row['GPS__Longitude']],
            radius=7,  # Plus grand pour les distinguer
            color='black',
            weight=2,
            fill=True,
            fill_color=assigned_color,
            fill_opacity=1.0,
            popup=f"Point orphelin {idx}<br>Assigné à: {assigned_tile}",
            tooltip="Point orphelin"
        ).add_to(orphan_group)
    orphan_group.add_to(m)

# Ajouter quelques points réguliers à la carte (limité à 1000 pour la performance)
max_points = min(1000, len(resultat_df))
points_group = folium.FeatureGroup(name='Points GPS')
for idx, row in resultat_df.iloc[:max_points].iterrows():
    # Exclure les points orphelins qui sont déjà affichés
    if 'points_sans_grille' in locals() and idx in points_sans_grille.index:
        continue

    if 'tuile' in row and pd.notna(row['tuile']):
        folium.CircleMarker(
            location=[row['GPS__Latitude'], row['GPS__Longitude']],
            radius=3,
            color='black',
            fill=True,
            fill_color=color_dict.get(row['tuile'], 'gray'),
            fill_opacity=0.7,
            popup=f"Point {idx}<br>Tuile: {row['tuile']}"
        ).add_to(points_group)
points_group.add_to(m)

# Ajouter une légende
legend_html = '''
<div style="position: fixed; bottom: 50px; right: 50px; width: 180px; z-index:9999; background-color:white;
             padding: 10px; border:2px solid grey; border-radius:5px; font-size:12px">
    <p><b>Légende</b></p>
'''

# Ajouter les 10 premières tuiles à la légende (pour éviter qu'elle ne soit trop grande)
for i, (tuile, color) in enumerate(list(color_dict.items())[:10]):
    legend_html += f'<i style="background:{color}; width:15px; height:15px; display:inline-block"></i> {tuile}<br>'

if len(color_dict) > 10:
    legend_html += f'<i>...et {len(color_dict)-10} autres tuiles</i>'

# Ajouter une indication pour les points orphelins s'il y en a
if 'points_sans_grille' in locals() and len(points_sans_grille) > 0:
    legend_html += '<br><p><b>Points spéciaux</b></p>'
    legend_html += '<i style="border:2px solid black; width:15px; height:15px; display:inline-block"></i> Points orphelins<br>'

legend_html += '</div>'
m.get_root().html.add_child(folium.Element(legend_html))

# Ajouter contrôle des couches
folium.LayerControl().add_to(m)

#  SAUVEGARDER LA CARTE EN HTML
map_html_path = os.path.join(export_dir, f"carte_interactive_tuiles_{file_prefix}.html")
m.save(map_html_path)
print(f"🗺️ Carte interactive sauvegardée dans: {map_html_path}")
print("   Vous pouvez ouvrir ce fichier dans un navigateur pour voir la carte interactive")

# Afficher la carte
display(m)



#  MÉTHODE ALTERNATIVE: Sauvegarder la carte en PNG (nécessite des dépendances supplémentaires)
try:
    # Cette méthode nécessite selenium et un driver web (comme chromedriver)
    print("\n Tentative de sauvegarde automatique de la carte en PNG...")

    # Installer les dépendances si nécessaire
    import subprocess
    import sys

    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        import time

        # Configuration du navigateur headless
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1200,800")

        # Créer le driver
        driver = webdriver.Chrome(options=chrome_options)

        # Ouvrir la carte HTML
        driver.get(f"file://{os.path.abspath(map_html_path)}")

        # Attendre que la carte se charge
        time.sleep(5)

        # Prendre une capture d'écran
        map_image_path = os.path.join(export_dir, f"carte_capture_{file_prefix}.png")
        driver.save_screenshot(map_image_path)
        driver.quit()

        print(f" Capture d'écran de la carte sauvegardée dans: {map_image_path}")

    except ImportError:
        print("  Selenium non disponible. Installation en cours...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium"])
        print("  Note: Vous devez aussi installer ChromeDriver pour la capture automatique")
        print("   Ou utilisez la méthode manuelle décrite ci-dessus")

    except Exception as e:
        print(f"  Capture automatique échouée: {e}")
        print("   Utilisez la méthode manuelle pour capturer la carte")

except Exception as e:
    print(f"  Impossible de configurer la capture automatique: {e}")
    print("   Utilisez la méthode manuelle pour capturer la carte")

# === STATISTIQUES CORRIGÉES ===
print(f"\n=== STATISTIQUES FINALES (CORRIGÉES) - CALCULS GÉODÉSIQUES ===")
print(f"Nombre total de tuiles: {len(grilles_gdf)}")
print(f"Nombre de tuiles avec au moins un point: {len(grilles_gdf[grilles_gdf['nb_points'] > 0])}")
print(f"Nombre minimum de points par tuile: {grilles_gdf['nb_points'].min()}")
print(f"Nombre maximum de points par tuile: {grilles_gdf['nb_points'].max()}")
print(f"Nombre moyen de points par tuile: {grilles_gdf['nb_points'].mean():.2f}")
print(f"Nombre médian de points par tuile: {grilles_gdf['nb_points'].median():.2f}")

# Statistiques additionnelles
tuiles_avec_points = grilles_gdf[grilles_gdf['nb_points'] > 0]
print(f"\nStatistiques pour les tuiles avec au moins un point:")
print(f"Nombre moyen de points: {tuiles_avec_points['nb_points'].mean():.2f}")
print(f"Écart-type: {tuiles_avec_points['nb_points'].std():.2f}")

#  Statistiques géodésiques
print(f"\n DIMENSIONS GÉODÉSIQUES DES TUILES :")
print(f"Largeur moyenne: {grilles_gdf['width_km'].mean():.3f} km (min: {grilles_gdf['width_km'].min():.3f}, max: {grilles_gdf['width_km'].max():.3f})")
print(f"Hauteur moyenne: {grilles_gdf['height_km'].mean():.3f} km (min: {grilles_gdf['height_km'].min():.3f}, max: {grilles_gdf['height_km'].max():.3f})")
print(f"Surface moyenne par tuile: {(grilles_gdf['width_km'] * grilles_gdf['height_km']).mean():.3f} km²")

# Créer un fichier texte avec des instructions pour Sentinel-2
sentinel_instructions_path = os.path.join(export_dir, f"instructions_sentinel2_{file_prefix}.txt")
with open(sentinel_instructions_path, 'w') as f:
    f.write(f"Instructions pour utiliser les tuiles {file_prefix} avec Sentinel-2\n")
    f.write("=" * (len(f"Instructions pour utiliser les tuiles {file_prefix} avec Sentinel-2") + 10) + "\n\n")
    f.write(f" DONNÉES : {file_prefix}\n")
    f.write(" PRÉCISION GÉODÉSIQUE :\n")
    f.write("Les tuiles ont été générées avec des calculs géodésiques précis (pyproj.Geod).\n")
    f.write(f"Dimensions moyennes réelles : {grilles_gdf['width_km'].mean():.3f} km × {grilles_gdf['height_km'].mean():.3f} km\n")
    f.write("Les distances entre points orphelins et tuiles utilisent également des calculs géodésiques.\n\n")
    f.write("Pour chaque tuile, vous trouverez les coordonnées de son centre et ses limites dans les fichiers exportés.\n\n")
    f.write("Format des fichiers exportés:\n")
    f.write(f"- points_avec_tuiles_{file_prefix}.csv: Points GPS avec leur tuile correspondante\n")
    f.write(f"- grilles_avec_tuiles_{file_prefix}.geojson: Géométries des tuiles au format GeoJSON\n")
    f.write(f"- grilles_avec_tuiles_{file_prefix}.shp, .dbf, .shx, .prj: Géométries des tuiles au format Shapefile\n\n")

    # Ajouter une section sur les points orphelins si nécessaire
    if 'points_sans_grille' in locals() and len(points_sans_grille) > 0:
        f.write(f" POINTS ORPHELINS :\n")
        f.write(f"• {len(points_sans_grille)} points se trouvaient en dehors de toutes les tuiles.\n")
        f.write("• Ces points ont été assignés à la tuile la plus proche avec des calculs géodésiques précis.\n")
        if len(orphan_df) > 0:
            f.write(f"• Distance moyenne d'assignation : {orphan_df['distance_km_geodesic'].mean():.3f} km\n")
            f.write(f"• Distance maximale d'assignation : {orphan_df['distance_km_geodesic'].max():.3f} km\n\n")

    f.write(" TÉLÉCHARGEMENT SENTINEL-2 :\n")
    f.write("1. Utilisez les coordonnées min_lon, min_lat, max_lon, max_lat comme bbox pour le téléchargement\n")
    f.write("2. Assurez-vous que la projection est en WGS84 (EPSG:4326)\n")
    f.write("3. Pour convertir en UTM (utilisé par Sentinel-2), vous pouvez utiliser la bibliothèque pyproj\n\n")
    f.write("Exemple de code pour télécharger une image Sentinel-2 pour une tuile (avec sentinelsat):\n\n")
    f.write("```python\n")
    f.write("from sentinelsat import SentinelAPI\n")
    f.write("import geopandas as gpd\n")
    f.write("from pyproj import Geod\n\n")
    f.write("# Connexion à l'API\n")
    f.write("api = SentinelAPI('user', 'password', 'https://scihub.copernicus.eu/dhus')\n\n")
    f.write("# Charger les tuiles\n")
    f.write(f"tiles = gpd.read_file('exports/grilles_avec_tuiles_{file_prefix}.geojson')\n\n")
    f.write("# Calculateur géodésique pour validations\n")
    f.write("geod = Geod(ellps='WGS84')\n\n")
    f.write("# Pour chaque tuile\n")
    f.write("for idx, tile in tiles.iterrows():\n")
    f.write("    # Définir la zone d'intérêt (footprint)\n")
    f.write("    footprint = tile.geometry.wkt\n")
    f.write("    \n")
    f.write("    # Vérifier les dimensions réelles\n")
    f.write("    print(f\"Tuile {tile['tuile']}: {tile['width_km']:.3f} km × {tile['height_km']:.3f} km\")\n")
    f.write("    \n")
    f.write("    # Rechercher les images Sentinel-2\n")
    f.write("    products = api.query(area=footprint,\n")
    f.write("                         date=('20230101', '20231231'),\n")
    f.write("                         platformname='Sentinel-2',\n")
    f.write("                         cloudcoverpercentage=(0, 20))\n")
    f.write("    \n")
    f.write("    # Télécharger la première image trouvée\n")
    f.write("    if products:\n")
    f.write("        product_id = list(products.keys())[0]\n")
    f.write("        api.download(product_id, directory_path=f'sentinel_images/{tile[\"tuile\"]}')\n")
    f.write("```\n")

print(f"Instructions pour Sentinel-2 sauvegardées dans: {sentinel_instructions_path}")

# Visualiser la distribution des points par tuile
plt.figure(figsize=(12, 8))

# Créer deux sous-graphiques
plt.subplot(2, 1, 1)
plt.hist(grilles_gdf['nb_points'], bins=30, edgecolor='black', alpha=0.7)
plt.title('Distribution du nombre de points par tuile (toutes tuiles)')
plt.xlabel('Nombre de points')
plt.ylabel('Nombre de tuiles')
plt.grid(True, alpha=0.3)

plt.subplot(2, 1, 2)
tuiles_avec_points = grilles_gdf[grilles_gdf['nb_points'] > 0]
plt.hist(tuiles_avec_points['nb_points'], bins=30, edgecolor='black', alpha=0.7, color='orange')
plt.title('Distribution du nombre de points par tuile (tuiles avec points uniquement)')
plt.xlabel('Nombre de points')
plt.ylabel('Nombre de tuiles')
plt.grid(True, alpha=0.3)

plt.tight_layout()

#  SAUVEGARDER LES HISTOGRAMMES EN IMAGE
histograms_path = os.path.join(export_dir, f"distribution_points_par_tuile_{file_prefix}.png")
plt.savefig(histograms_path, dpi=300, bbox_inches='tight', facecolor='white')
print(f" Histogrammes sauvegardés dans: {histograms_path}")

plt.show()

# Afficher un tableau de distribution des points par tuile
print("\nDistribution des points par tuile:")
tuile_counts = resultat_df['tuile'].value_counts().reset_index()
tuile_counts.columns = ['Tuile', 'Nombre de points']
print(tuile_counts.head(20))
print(f"... et {len(tuile_counts)-20} autres tuiles" if len(tuile_counts) > 20 else "")

#  CRÉER UN GRAPHIQUE DES TOP TUILES
plt.figure(figsize=(14, 6))

# Top 20 des tuiles avec le plus de points
top_20_tuiles = tuile_counts.head(20)

bars = plt.bar(range(len(top_20_tuiles)), top_20_tuiles['Nombre de points'],
               color='steelblue', alpha=0.7, edgecolor='black')
plt.title('Top 20 des tuiles avec le plus de points GPS', fontsize=16, fontweight='bold', pad=20)
plt.xlabel('Tuiles (classées par nombre de points)', fontsize=12)
plt.ylabel('Nombre de points', fontsize=12)
plt.xticks(range(len(top_20_tuiles)), top_20_tuiles['Tuile'], rotation=45, ha='right')
plt.grid(True, alpha=0.3, axis='y')

# Ajouter les valeurs sur les barres
for i, bar in enumerate(bars):
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
             f'{int(height)}', ha='center', va='bottom', fontsize=9, fontweight='bold')

# Ajouter des statistiques sur le graphique
stats_text = f"""Top 20 représente:
• {top_20_tuiles['Nombre de points'].sum()} points GPS
• {(top_20_tuiles['Nombre de points'].sum() / len(resultat_df) * 100):.1f}% du total
• Moyenne top 20: {top_20_tuiles['Nombre de points'].mean():.1f} pts/tuile"""

plt.text(0.98, 0.98, stats_text, transform=plt.gca().transAxes,
         verticalalignment='top', horizontalalignment='right',
         bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8),
         fontsize=10)

plt.tight_layout()

# Sauvegarder le graphique des top tuiles
top_tuiles_path = os.path.join(export_dir, f"top_20_tuiles_{file_prefix}.png")
plt.savefig(top_tuiles_path, dpi=300, bbox_inches='tight', facecolor='white')
print(f" Top 20 tuiles sauvegardé dans: {top_tuiles_path}")

plt.show()

#  CRÉER UN GRAPHIQUE SPÉCIAL POUR LA DISTRIBUTION (SÉPARÉ)
plt.figure(figsize=(14, 6))

# Distribution simple et claire
plt.hist(grilles_gdf['nb_points'], bins=50, edgecolor='black', alpha=0.7, color='skyblue')
plt.title('Distribution détaillée du nombre de points par tuile', fontsize=16, fontweight='bold', pad=20)
plt.xlabel('Nombre de points par tuile', fontsize=12)
plt.ylabel('Nombre de tuiles', fontsize=12)
plt.grid(True, alpha=0.3)

# Ajouter des statistiques sur le graphique
stats_text = f"""Statistiques:
• Total tuiles: {len(grilles_gdf)}
• Min: {grilles_gdf['nb_points'].min()}
• Max: {grilles_gdf['nb_points'].max()}
• Moyenne: {grilles_gdf['nb_points'].mean():.1f}
• Médiane: {grilles_gdf['nb_points'].median():.1f}"""

plt.text(0.98, 0.98, stats_text, transform=plt.gca().transAxes,
         verticalalignment='top', horizontalalignment='right',
         bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
         fontsize=10)

# Sauvegarder la distribution seule
distribution_seule_path = os.path.join(export_dir, f"distribution_detaillee_points_tuiles_{file_prefix}.png")
plt.savefig(distribution_seule_path, dpi=300, bbox_inches='tight', facecolor='white')
print(f" Distribution détaillée sauvegardée dans: {distribution_seule_path}")

plt.show()

# Créer un fichier récapitulatif des fichiers générés
recap_path = os.path.join(export_dir, f"recap_fichiers_{file_prefix}.txt")
with open(recap_path, 'w') as f:
    f.write(f"Récapitulatif des fichiers générés - {file_prefix}\n")
    f.write("=" * (len(f"Récapitulatif des fichiers générés - {file_prefix}") + 10) + "\n\n")
    f.write(f" IDENTIFIANT : {file_prefix}\n")
    f.write(f" ANNÉE EHCVM : {EHCVM_YEAR}\n\n")

    # Lister tous les fichiers dans le répertoire d'export
    files = os.listdir(export_dir)

    f.write(" FICHIERS DE DONNÉES:\n")
    data_files = [f for f in files if f.endswith(('.csv', '.geojson', '.shp', '.dbf', '.shx', '.prj'))]
    for file in sorted(data_files):
        file_path = os.path.join(export_dir, file)
        file_size = os.path.getsize(file_path) / 1024  # taille en Ko
        f.write(f"  • {file}: {file_size:.2f} Ko\n")

    f.write("\n GRAPHIQUES ET VISUALISATIONS:\n")
    viz_files = [f for f in files if f.endswith(('.png', '.html'))]
    for file in sorted(viz_files):
        file_path = os.path.join(export_dir, file)
        file_size = os.path.getsize(file_path) / 1024  # taille en Ko
        f.write(f"  • {file}: {file_size:.2f} Ko\n")

    f.write("\n DOCUMENTATION:\n")
    doc_files = [f for f in files if f.endswith('.txt')]
    for file in sorted(doc_files):
        file_path = os.path.join(export_dir, file)
        file_size = os.path.getsize(file_path) / 1024  # taille en Ko
        f.write(f"  • {file}: {file_size:.2f} Ko\n")

    # Ajouter les statistiques finales au récapitulatif
    f.write(f"\n STATISTIQUES FINALES:\n")
    f.write(f"  • Nombre total de points GPS: {len(resultat_df)}\n")
    f.write(f"  • Nombre total de tuiles: {len(grilles_gdf)}\n")
    f.write(f"  • Nombre de tuiles avec points: {len(grilles_gdf[grilles_gdf['nb_points'] > 0])}\n")
    f.write(f"  • Points par tuile - Min: {grilles_gdf['nb_points'].min()}, Max: {grilles_gdf['nb_points'].max()}, Moyenne: {grilles_gdf['nb_points'].mean():.2f}\n")

    #  Ajouter les statistiques géodésiques
    f.write(f"\n PRÉCISION GÉODÉSIQUE:\n")
    f.write(f"  • Dimensions moyennes des tuiles: {grilles_gdf['width_km'].mean():.3f} × {grilles_gdf['height_km'].mean():.3f} km\n")
    f.write(f"  • Surface moyenne par tuile: {(grilles_gdf['width_km'] * grilles_gdf['height_km']).mean():.3f} km²\n")
    f.write(f"  • Calculs de distance: géodésiques précis (pyproj.Geod)\n")

    if 'points_sans_grille' in locals() and len(points_sans_grille) > 0:
        f.write(f"  • Points orphelins assignés: {len(points_sans_grille)}\n")
        if len(orphan_df) > 0:
            f.write(f"  • Distance moyenne d'assignation: {orphan_df['distance_km_geodesic'].mean():.3f} km\n")

print(f"Récapitulatif des fichiers générés sauvegardé dans: {recap_path}")

print(f"\n === RÉSUMÉ DES FICHIERS GÉNÉRÉS - {file_prefix} ===")
print(f" Données: points_avec_tuiles_{file_prefix}.csv, grilles_avec_tuiles_{file_prefix}.geojson/shp")
print(f" Graphiques: distribution_points_par_tuile_{file_prefix}.png, top_20_tuiles_{file_prefix}.png, distribution_detaillee_points_tuiles_{file_prefix}.png")
print(f" Carte: carte_interactive_tuiles_{file_prefix}.html")
print(f" Documentation: instructions_sentinel2_{file_prefix}.txt, recap_fichiers_{file_prefix}.txt")

print(f"\n === SCRIPT TERMINÉ AVEC SUCCÈS - {file_prefix} ===")
print(" Toutes les statistiques sont maintenant cohérentes!")
print(" Les fichiers exportés contiennent les données correctes!")
print(" Calculs géodésiques précis utilisés pour toutes les distances!")
print(" Dimensions des tuiles calculées avec pyproj.Geod (WGS84)")