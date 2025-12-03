"""
==================================================================================
GÉNÉRATEUR DE GRILLE GÉODÉSIQUE OPTIMISÉE POUR L'AFRIQUE
==================================================================================

"""
import os
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Point, Polygon
import matplotlib.pyplot as plt
from pyproj import Geod
import time

# ================================================================
# === CONFIGURATION PARAMÈTRES - MODIFIEZ ICI VOS VALEURS ===
# ================================================================
# PARAMÈTRE PRINCIPAL : Taille des carrés en kilomètres
SQUARE_SIZE_KM = 2.24  # Changez cette valeur selon vos besoins (ex: 2.27, 3.0, 1.5, etc.)

# Distance pour les points cardinaux (égale à la taille du carré pour éviter chevauchement)
CARDINAL_DISTANCE_KM = SQUARE_SIZE_KM  # Maintenant défini pour que les bords se touchent mais ne chevauchent pas

# Paramètres de visualisation
SAMPLE_SIZE_FOR_SQUARES_VISUALIZATION = 20  # Nombre de carrés à afficher dans l'exemple
MARGIN_FACTOR_FOR_DETAIL = 2.0  # Facteur de marge pour le zoom détaillé

# Paramètres de fichiers (modifiés automatiquement selon la taille)
SIZE_STR = str(SQUARE_SIZE_KM).replace('.', '')  # Ex: "224" pour 2.24
INPUT_FILENAME = 'df_afrique_coordonnees_consolidees.csv'
AFRICA_FILENAME = 'africa.json'

print(f"Configuration active:")
print(f"  - Taille des carrés: {SQUARE_SIZE_KM} km × {SQUARE_SIZE_KM} km")
print(f"  - Distance points cardinaux: {CARDINAL_DISTANCE_KM} km")
print(f"  - Surface par carré: {SQUARE_SIZE_KM**2:.3f} km²")

# ================================================================
# === VÉRIFICATION ET INSTALLATION GPU (GOOGLE COLAB) ===
# ================================================================
GPU_AVAILABLE = False
try:
    import subprocess
    import sys

    # Vérifier si on est sur Colab
    if 'COLAB_GPU' in os.environ:
        print("\n Environnement Google Colab détecté...")
        try:
            gpu_info = subprocess.check_output(['nvidia-smi'], stderr=subprocess.DEVNULL)
            print("✓ GPU détecté!")

            # Installer CuPy pour l'accélération GPU
            try:
                import cupy as cp
                print("✓ CuPy déjà installé")
                GPU_AVAILABLE = True
            except ImportError:
                print("Installation de CuPy pour accélération GPU...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "cupy-cuda11x", "-q"])
                import cupy as cp
                print("✓ CuPy installé avec succès!")
                GPU_AVAILABLE = True

        except subprocess.CalledProcessError:
            print("✗ Pas de GPU détecté - utilisation du CPU")
    else:
        print("\n Environnement local détecté - utilisation du CPU")

except Exception as e:
    print(f" Erreur lors de la vérification GPU: {e}")
    print("Utilisation du CPU par défaut")

# ================================================================
# === INSTALLATION DE FOLIUM POUR LA CARTE INTERACTIVE ===
# ================================================================
try:
    import folium
    print("✓ Folium disponible pour la carte interactive")
except ImportError:
    print(" Installation de Folium pour la carte interactive...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "folium", "-q"])
        import folium
        print("✓ Folium installé avec succès!")
    except Exception as e:
        print(f" Erreur lors de l'installation de Folium: {e}")
        print("La carte interactive ne sera pas disponible")
        folium = None

# ================================================================
# === CONFIGURATION DES RÉPERTOIRES ===
# ================================================================
if 'COLAB_GPU' in os.environ:
    from google.colab import drive
    drive.mount('/content/drive')
    base_directory = os.path.join('/content', 'drive', 'MyDrive')
else:
    base_directory = os.path.expanduser(os.path.join('~', 'Documents', 'coordonnees_project'))
    os.makedirs(base_directory, exist_ok=True)

print(f"Répertoire de base utilisé: {base_directory}")

# === DÉFINITION DES CHEMINS DE FICHIERS (DYNAMIQUES) ===
csv_path = os.path.join(base_directory, INPUT_FILENAME)
africa_geojson = os.path.join(base_directory, AFRICA_FILENAME)
output_data_filename = f'coordonnees_grid_points_{SIZE_STR}km.csv'
output_data_path = os.path.join(base_directory, output_data_filename)
map_image_filename = f'coordonnees_grid_visualization_{SIZE_STR}km_with_africa_map.png'
simple_map_filename = f'coordonnees_grid_visualization_{SIZE_STR}km_simple.png'

# Nouveaux fichiers d'export
output_geojson_path = os.path.join(base_directory, f'carres_geodesiques_{SIZE_STR}km.geojson')
output_shapefile_path = os.path.join(base_directory, f'carres_geodesiques_{SIZE_STR}km.shp')
output_html_map_path = os.path.join(base_directory, f'carte_interactive_carres_{SIZE_STR}km.html')

# === VÉRIFICATION DE L'EXISTENCE DES FICHIERS ===
if not os.path.exists(csv_path):
    print(f"ERREUR: Le fichier {csv_path} n'existe pas!")
    if 'COLAB_GPU' in os.environ:
        print("Recherche du fichier dans Google Drive...")
        os.system(f"find /content/drive -type f -iname '{INPUT_FILENAME}'")
    else:
        print(f"Veuillez placer le fichier '{INPUT_FILENAME}' dans le répertoire: {base_directory}")
    exit(1)

print(f"Fichier d'entrée trouvé: {csv_path}")

# === CHARGEMENT ET TRAITEMENT DES DONNÉES ===
df = pd.read_csv(csv_path)
required_columns = ['latitude', 'longitude']
missing_columns = [col for col in required_columns if col not in df.columns]
if missing_columns:
    print(f"ERREUR: Colonnes manquantes dans le fichier CSV: {missing_columns}")
    print(f"Colonnes disponibles: {list(df.columns)}")
    exit(1)

df['name'] = [f'point_{i}' for i in range(len(df))]
df['city'] = 'unknown'

print(f"Nombre de points originaux: {len(df)}")
geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
geod = Geod(ellps='WGS84')

# ================================================================
# === FONCTIONS GÉODÉSIQUES CONFIGURABLES ===
# ================================================================
def create_cardinal_points_geodesic(row, distance_km=CARDINAL_DISTANCE_KM):
    """
    Crée des points cardinaux à une distance géodésique donnée.
    Ici, distance_km = taille du côté du carré pour que seuls les bords se touchent.
    """
    original_point = row.geometry
    lon, lat = original_point.x, original_point.y
    distance_m = distance_km * 1000

    lon_north, lat_north, _ = geod.fwd(lon, lat, 0, distance_m)
    lon_east, lat_east, _   = geod.fwd(lon, lat, 90, distance_m)
    lon_south, lat_south, _ = geod.fwd(lon, lat, 180, distance_m)
    lon_west, lat_west, _   = geod.fwd(lon, lat, 270, distance_m)

    return pd.Series({
        'original': original_point,
        'north': Point(lon_north, lat_north),
        'east':  Point(lon_east, lat_east),
        'south': Point(lon_south, lat_south),
        'west':  Point(lon_west, lat_west)
    })

def create_geodesic_square_aligned(point, size_km=SQUARE_SIZE_KM):
    """
    Crée un carré géodésique de côté size_km autour d'un point,
    avec les côtés parallèles aux axes lat/lon.
    On calcule d'abord les points 'nord' et 'sud' à half_side, puis
    on part de ces points pour calculer 'ouest' et 'est' à half_side.
    """
    lon, lat = point.x, point.y
    half_side_m = (size_km * 1000) / 2

    # 1. On place le point à moitié du côté au Nord et au Sud
    lon_north, lat_north, _ = geod.fwd(lon, lat, 0, half_side_m)
    lon_south, lat_south, _ = geod.fwd(lon, lat, 180, half_side_m)

    # 2. À partir de ces deux points, on se déplace à l'Ouest et à l'Est pour définir les coins
    lon_nw, lat_nw, _ = geod.fwd(lon_north, lat_north, 270, half_side_m)
    lon_ne, lat_ne, _ = geod.fwd(lon_north, lat_north, 90, half_side_m)
    lon_sw, lat_sw, _ = geod.fwd(lon_south, lat_south, 270, half_side_m)
    lon_se, lat_se, _ = geod.fwd(lon_south, lat_south, 90, half_side_m)

    square_coords = [
        (lon_nw, lat_nw),
        (lon_ne, lat_ne),
        (lon_se, lat_se),
        (lon_sw, lat_sw),
        (lon_nw, lat_nw)
    ]
    return Polygon(square_coords)

def calculate_geodesic_area(polygon):
    """
    Calcule l'aire géodésique d'un polygone en km².
    """
    if polygon.is_empty:
        return 0.0
    coords = list(polygon.exterior.coords)
    lons = [coord[0] for coord in coords]
    lats = [coord[1] for coord in coords]
    area_m2 = abs(geod.polygon_area_perimeter(lons, lats)[0])
    return area_m2 / 1_000_000  # en km²

# ================================================================
# === DÉTECTION DES CHEVAUCHEMENTS GPU/CPU ===
# ================================================================
def detect_overlaps_gpu(squares_gdf):
    """
    Détection des chevauchements en utilisant le GPU avec CuPy.
    (on ignore les carrés qui ne font que se toucher).
    """
    import cupy as cp

    print("🚀 Préparation des données pour traitement GPU...")
    bounds = np.array([geom.bounds for geom in squares_gdf.geometry])
    n = len(bounds)
    bounds_gpu = cp.asarray(bounds)

    print(f"📊 Analyse de {n} carrés sur GPU...")

    # On remplace >=/<= par >/< pour ne pas compter les bords en contact
    minx1 = bounds_gpu[:, 0:1]
    miny1 = bounds_gpu[:, 1:2]
    maxx1 = bounds_gpu[:, 2:3]
    maxy1 = bounds_gpu[:, 3:4]

    minx2 = bounds_gpu[:, 0]
    miny2 = bounds_gpu[:, 1]
    maxx2 = bounds_gpu[:, 2]
    maxy2 = bounds_gpu[:, 3]

    overlap_matrix = (
        (maxx1 > minx2) & (minx1 < maxx2) &
        (maxy1 > miny2) & (miny1 < maxy2)
    )

    overlap_cpu = cp.asnumpy(overlap_matrix)
    overlaps = []
    for i in range(n):
        if i % 1000 == 0 and i > 0:
            print(f"  Vérification précise: {i}/{n} ({i/n*100:.1f}%)")
        for j in range(i + 1, n):
            if overlap_cpu[i, j]:
                # Ne conserver que si la surface d'intersection est strictement positive
                if squares_gdf.geometry[i].overlaps(squares_gdf.geometry[j]):
                    overlaps.append((i, j))

    print(f"✓ {len(overlaps)} chevauchements détectés via GPU")
    return overlaps

def detect_overlaps_cpu_optimized(squares_gdf):
    """
    Version CPU optimisée avec index spatial pour fallback.
    (on ignore les carrés qui ne font que se toucher).
    """
    print(" Détection des chevauchements sur CPU (optimisé)...")
    overlaps = []
    n_squares = len(squares_gdf)

    for i in range(n_squares):
        if i % 500 == 0 and i > 0:
            print(f"  Progression: {i}/{n_squares} ({i/n_squares*100:.1f}%)")
        current_geom = squares_gdf.geometry.iloc[i]
        candidates = list(squares_gdf.sindex.intersection(current_geom.bounds))
        for j in candidates:
            if j > i:
                # Ne conserver que si la surface d'intersection est > 0
                if current_geom.overlaps(squares_gdf.geometry.iloc[j]):
                    overlaps.append((i, j))
    print(f"✓ {len(overlaps)} chevauchements détectés via CPU")
    return overlaps

# ================================================================
# === NOUVELLE FONCTION D'ÉLIMINATION PAR INDEPENDANT SET ===
# ================================================================
def eliminate_overlaps_independent_set(overlaps, n_squares):
    """
    Sélectionne un ensemble indépendant maximal de carrés, c'est-à-dire
    un sous-ensemble où aucun carré ne se chevauche.
    Pour chaque carré, on l'ajoute s'il ne chevauche aucun des carrés déjà gardés.
    """
    print("🔄 Élimination des chevauchements par independent set...")
    # Construire un dictionnaire de voisins pour accès rapide
    neighbors = {i: set() for i in range(n_squares)}
    for i, j in overlaps:
        neighbors[i].add(j)
        neighbors[j].add(i)

    # On va parcourir les indices dans un ordre fixe (purement croissant ou aléatoire)
    indices = list(range(n_squares))
    # On peut mélanger l'ordre si on veut un choix aléatoire : np.random.shuffle(indices)
    # np.random.shuffle(indices)

    kept = []
    kept_set = set()
    for idx in indices:
        # On vérifie si idx chevauche un carré déjà gardé
        conflict = False
        for k in neighbors[idx]:
            if k in kept_set:
                conflict = True
                break
        if not conflict:
            kept.append(idx)
            kept_set.add(idx)

    print(f"✓ {len(kept)} carrés conservés après independent set")
    return kept

# ================================================================
# === TRAITEMENT PRINCIPAL ===
# ================================================================
print(f"\n📍 Création des points cardinaux à {CARDINAL_DISTANCE_KM} km...")
cardinal_points = gdf.apply(create_cardinal_points_geodesic, axis=1)

all_centers = []
for idx, row in gdf.iterrows():
    # On ajoute le point original
    all_centers.append({
        'name': row['name'],
        'city': row['city'],
        'geometry': row.geometry,
        'point_type': 'original'
    })
    # On ajoute les 4 points cardinaux (nord, est, sud, ouest)
    for direction in ['north', 'east', 'south', 'west']:
        all_centers.append({
            'name': f"{row['name']}_{direction}",
            'city': row['city'],
            'geometry': cardinal_points.loc[idx, direction],
            'point_type': direction
        })

all_centers_gdf = gpd.GeoDataFrame(all_centers, crs="EPSG:4326")
print(f"\n Création des carrés géodésiques ({len(all_centers_gdf)} centres)...")
all_centers_gdf['square'] = all_centers_gdf.geometry.apply(
    lambda pt: create_geodesic_square_aligned(pt, size_km=SQUARE_SIZE_KM)
)

start_time = time.time()
squares_gdf = gpd.GeoDataFrame(
    {'id': range(len(all_centers_gdf)), 'geometry': all_centers_gdf['square']},
    crs=all_centers_gdf.crs
)

print(f"\n Détection des chevauchements parmi {len(squares_gdf)} carrés...")
if GPU_AVAILABLE:
    try:
        overlaps = detect_overlaps_gpu(squares_gdf)
    except Exception as e:
        print(f" Erreur GPU: {e}\nBasculement sur CPU…")
        overlaps = detect_overlaps_cpu_optimized(squares_gdf)
else:
    overlaps = detect_overlaps_cpu_optimized(squares_gdf)

print(f"\n Nombre total de chevauchements détectés: {len(overlaps)}")
to_keep = eliminate_overlaps_independent_set(overlaps, len(all_centers_gdf))
elapsed_time = time.time() - start_time
print(f"\n Temps de traitement: {elapsed_time:.2f} secondes")
print(f" Performance: {len(squares_gdf)/elapsed_time:.0f} carrés/seconde")
if len(squares_gdf) > 1000:
    estimated_original_time = (len(squares_gdf)**2) / 10000
    speedup = estimated_original_time / elapsed_time
    print(f"📈 Accélération estimée: {speedup:.1f}x par rapport à la méthode originale")

filtered_centers = all_centers_gdf.iloc[to_keep].copy()
filtered_centers['latitude'] = filtered_centers.geometry.y
filtered_centers['longitude'] = filtered_centers.geometry.x

# Validation des aires
if len(filtered_centers) > 0:
    sample_squares = filtered_centers.head(5)['square']
    actual_areas = [calculate_geodesic_area(sq) for sq in sample_squares]
    theoretical_area = SQUARE_SIZE_KM**2
    print(f"\n Validation des aires (échantillon de 5 carrés):")
    print(f"  Aire théorique: {theoretical_area:.3f} km²")
    print(f"  Aires réelles: {[f'{area:.3f}' for area in actual_areas]} km²")
    print(f"  Différence moyenne: {abs(np.mean(actual_areas) - theoretical_area):.3f} km²")
else:
    print("\n Aucun carré n'a été conservé après filtrage (vérifiez vos distances et chevauchements).")

# Enrichir l'export CSV avec les mêmes métadonnées que les autres formats
output_df = filtered_centers[['name', 'city', 'latitude', 'longitude', 'point_type']].copy()
output_df['square_size_km'] = SQUARE_SIZE_KM
output_df['area_km2'] = filtered_centers['square'].apply(calculate_geodesic_area)
output_df['center_lat'] = filtered_centers['latitude']
output_df['center_lon'] = filtered_centers['longitude']

output_df.to_csv(output_data_path, index=False)

print(f"\n Résumé:")
print(f"  Points originaux: {len(df)}")
print(f"  Points candidats totaux: {len(all_centers_gdf)}")
print(f"  Points conservés après filtrage: {len(filtered_centers)}")
print(f"  Taux de conservation: {len(filtered_centers)/len(all_centers_gdf)*100 if len(all_centers_gdf)>0 else 0:.2f}%")

# ================================================================
# === EXPORT EN GEOJSON ET SHAPEFILE ===
# ================================================================
if len(filtered_centers) > 0:
    print(f"\n Export des carrés géodésiques...")

    # Créer un GeoDataFrame avec les carrés comme géométrie
    squares_export_gdf = gpd.GeoDataFrame(
        filtered_centers[['name', 'city', 'latitude', 'longitude', 'point_type']],
        geometry=filtered_centers['square'],
        crs="EPSG:4326"
    )

    # Ajouter des métadonnées utiles
    squares_export_gdf['square_size_km'] = SQUARE_SIZE_KM
    squares_export_gdf['area_km2'] = squares_export_gdf.geometry.apply(calculate_geodesic_area)
    squares_export_gdf['center_lat'] = filtered_centers['latitude']
    squares_export_gdf['center_lon'] = filtered_centers['longitude']

    # Export en GeoJSON
    try:
        squares_export_gdf.to_file(output_geojson_path, driver='GeoJSON')
        print(f"✓ Export GeoJSON réussi: {output_geojson_path}")
    except Exception as e:
        print(f" Erreur export GeoJSON: {e}")

    # Export en Shapefile
    try:
        squares_export_gdf.to_file(output_shapefile_path, driver='ESRI Shapefile')
        print(f"✓ Export Shapefile réussi: {output_shapefile_path}")
    except Exception as e:
        print(f" Erreur export Shapefile: {e}")

# ================================================================
# === CRÉATION DE LA CARTE INTERACTIVE HTML ===
# ================================================================
if folium is not None and len(filtered_centers) > 0:
    print(f"\n Création de la carte interactive HTML...")

    # Calculer le centre de la carte
    center_lat = filtered_centers['latitude'].mean()
    center_lon = filtered_centers['longitude'].mean()

    # Créer la carte de base
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=6,
        tiles='OpenStreetMap'
    )

    # Ajouter les carrés à la carte
    colors = {
        'original': 'red',
        'north': 'blue',
        'east': 'green',
        'south': 'orange',
        'west': 'purple'
    }

    print(f"  Ajout de {len(filtered_centers)} carrés à la carte...")
    for idx, row in filtered_centers.iterrows():
        # Convertir le carré en coordonnées pour folium
        square_coords = list(row['square'].exterior.coords)
        folium_coords = [[coord[1], coord[0]] for coord in square_coords[:-1]]  # Inverser lon/lat

        color = colors.get(row['point_type'], 'gray')

        # Ajouter le carré
        folium.Polygon(
            locations=folium_coords,
            popup=f"""
            <b>{row['name']}</b><br>
            Type: {row['point_type']}<br>
            Ville: {row['city']}<br>
            Centre: {row['latitude']:.6f}, {row['longitude']:.6f}<br>
            Taille: {SQUARE_SIZE_KM} km × {SQUARE_SIZE_KM} km
            """,
            tooltip=f"{row['name']} ({row['point_type']})",
            color=color,
            weight=2,
            opacity=0.8,
            fillColor=color,
            fillOpacity=0.3
        ).add_to(m)

        # Ajouter un marqueur au centre
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=3,
            popup=f"{row['name']} - {row['point_type']}",
            color=color,
            fillColor=color,
            fillOpacity=0.8
        ).add_to(m)

    # Ajouter une légende
    legend_html = f'''
    <div style="position: fixed;
                top: 10px; right: 10px; width: 200px; height: 160px;
                background-color: white; border:2px solid grey; z-index:9999;
                font-size:14px; padding: 10px">
    <h4>Carrés Géodésiques {SQUARE_SIZE_KM} km</h4>
    <p><i class="fa fa-square" style="color:red"></i> Points originaux</p>
    <p><i class="fa fa-square" style="color:blue"></i> Points Nord</p>
    <p><i class="fa fa-square" style="color:green"></i> Points Est</p>
    <p><i class="fa fa-square" style="color:orange"></i> Points Sud</p>
    <p><i class="fa fa-square" style="color:purple"></i> Points Ouest</p>
    <p><b>Total: {len(filtered_centers)} carrés</b></p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    # Sauvegarder la carte
    try:
        m.save(output_html_map_path)
        print(f" Carte interactive HTML créée: {output_html_map_path}")
    except Exception as e:
        print(f" Erreur création carte HTML: {e}")

elif folium is None:
    print(f"\n Folium non disponible - carte interactive non créée")
else:
    print(f"\n Aucun carré à afficher sur la carte interactive")

# === CHARGEMENT DU FOND DE CARTE AFRICAIN ===
try:
    africa = gpd.read_file(africa_geojson)
    print(f"\n Nombre de géométries dans africa.json : {len(africa)}")
    map_available = True
except Exception as e:
    print(f"\n Impossible de charger africa.json : {e}")
    print("Visualisation simple sans fond de carte sera générée.")
    map_available = False

# ================================================================
# === VISUALISATION PRINCIPALE (SEULE VISUALISATION CONSERVÉE) ===
# ================================================================
if len(filtered_centers) > 0:
    fig, ax = plt.subplots(figsize=(15, 15))
    if map_available:
        africa.boundary.plot(ax=ax, linewidth=1, color='gray', alpha=0.8)
        map_title = f'Points GPS conservés (carrés {SQUARE_SIZE_KM} km) avec fond de carte africain'
        save_filename = map_image_filename
    else:
        map_title = f'Points GPS conservés (carrés {SQUARE_SIZE_KM} km) sans fond de carte'
        save_filename = simple_map_filename

    save_path = os.path.join(base_directory, save_filename)
    filtered_centers.plot(ax=ax, markersize=8, column='point_type', legend=True,
                         categorical=True, cmap='viridis', alpha=0.8)
    plt.title(map_title, fontsize=16)
    plt.xlabel('Longitude', fontsize=12)
    plt.ylabel('Latitude', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()

# ================================================================
# === STATISTIQUES ET RÉSUMÉ DYNAMIQUES ===
# ================================================================
print("\n" + "="*70)
print(f"RÉSUMÉ DES RÉSULTATS - CARRÉS GÉODÉSIQUES {SQUARE_SIZE_KM} km × {SQUARE_SIZE_KM} km")
print("="*70)

print(f"\n Configuration utilisée:")
print(f"  Taille des carrés: {SQUARE_SIZE_KM} km × {SQUARE_SIZE_KM} km")
print(f"  Distance points cardinaux: {CARDINAL_DISTANCE_KM} km")
print(f"  Surface théorique par carré: {SQUARE_SIZE_KM**2:.3f} km²")
print(f"  Méthode de calcul: {'GPU (CuPy)' if GPU_AVAILABLE else 'CPU (Optimisé)'}")

print("\n Aperçu des 5 premières lignes:")
if len(filtered_centers) > 0:
    print(filtered_centers[['name', 'latitude', 'longitude', 'point_type']].head(5))
else:
    print("  Aucun carré à afficher.")

print("\n Répartition par type de point:")
if len(filtered_centers) > 0:
    type_counts = filtered_centers['point_type'].value_counts()
    for point_type, count in type_counts.items():
        percentage = (count / len(filtered_centers)) * 100
        print(f"  {point_type}: {count} ({percentage:.1f}%)")
else:
    print("  Aucun carré conservé.")

print("\n Statistiques géographiques:")
if len(filtered_centers) > 0:
    print(f"  Latitude min: {filtered_centers['latitude'].min():.6f}")
    print(f"  Latitude max: {filtered_centers['latitude'].max():.6f}")
    print(f"  Longitude min: {filtered_centers['longitude'].min():.6f}")
    print(f"  Longitude max: {filtered_centers['longitude'].max():.6f}")
else:
    print("  Pas de coordonnées à afficher.")

print(f"\n Surface totale couverte:")
print(f"  Nombre de carrés: {len(filtered_centers)}")
print(f"  Taille de chaque carré: {SQUARE_SIZE_KM} km × {SQUARE_SIZE_KM} km = {SQUARE_SIZE_KM**2:.3f} km²")
print(f"  Surface totale: {len(filtered_centers)*(SQUARE_SIZE_KM**2):.2f} km²")

print(f"\n Fichiers générés dans {base_directory}:")
print(f"  - Données CSV enrichies: {output_data_filename}")
print(f"    (avec métadonnées: taille, aire, coordonnées centre)")
print(f"  - Export GeoJSON: carres_geodesiques_{SIZE_STR}km.geojson")
print(f"  - Export Shapefile: carres_geodesiques_{SIZE_STR}km.shp")
print(f"  - Carte interactive HTML: carte_interactive_carres_{SIZE_STR}km.html")
if map_available:
    print(f"  - Carte principale: {map_image_filename}")
else:
    print(f"  - Carte principale: {simple_map_filename}")

print(f"\n Répertoire de travail: {base_directory}")

print("\n" + "="*70)
print("⚡ OPTIMISATION GPU/CPU ACTIVÉE")
print("="*70)
if GPU_AVAILABLE:
    print("✓ GPU détecté et utilisé pour l'accélération")
    print("  Les calculs de chevauchements ont été effectués sur GPU")
else:
    print("✓ CPU optimisé utilisé (index spatial R-tree)")
    print("  Pour activer le GPU sur Google Colab:")
    print("  Runtime → Change runtime type → GPU")
print("="*70)

