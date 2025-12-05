
import os
import pandas as pd
import numpy as np
from sklearn.mixture import GaussianMixture
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
import rasterio
from rasterio.windows import from_bounds


# Chemin vers votre CSV de grilles 224km
csv_file_path = r"D:\wealth_predict_sentinel_v2\data\output\processed_csv\coordonnees_grid_points_224km.csv"
df = pd.read_csv(csv_file_path)

# Chemin vers votre fichier TIFF de radiance nocturne
tif_file_path = r"D:\wealth_predict_sentinel_v2\data\downloaded\VNL_npp_2023_global_vcmslcfg_v2_c202402081600.average.dat.tif"

# Ouvrir le raster
with rasterio.open(tif_file_path) as dataset:
    raster = dataset.read(1)
    transform = dataset.transform
    nodata = dataset.nodata

    def mean_radiance_in_square(lon, lat, square_size_km):
        """
        Calcule la moyenne de radiance dans un carré centré sur (lon, lat)
        de côté = square_size_km kilomètres.
        """
        # Conversion de la taille du carré en mètres
        size_m = square_size_km * 1000.0
        half_m = size_m / 2.0

        # Conversion approximative mètres → degrés
        # 1° ≃ 111 320 m en longitude, 1° ≃ 110 540 m en latitude
        deg_x = half_m / 111_320.0
        deg_y = half_m / 110_540.0

        # Bornes géographiques du carré
        min_lon, max_lon = lon - deg_x, lon + deg_x
        min_lat, max_lat = lat - deg_y, lat + deg_y

        # Calcul de la fenêtre en pixels
        window = from_bounds(min_lon, min_lat, max_lon, max_lat, transform)

        # Extraction des indices entiers et bornage
        row_off = max(int(window.row_off), 0)
        col_off = max(int(window.col_off), 0)
        height  = int(window.height)
        width   = int(window.width)

        # S'assurer de ne pas dépasser le raster
        if row_off + height > raster.shape[0]:
            height = raster.shape[0] - row_off
        if col_off + width > raster.shape[1]:
            width = raster.shape[1] - col_off

        # Lecture des données
        data = raster[row_off:row_off + height, col_off:col_off + width].astype(float)

        # Masquage des valeurs no-data
        if nodata is not None:
            data[data == nodata] = np.nan

        # Si la fenêtre est hors du raster
        if data.size == 0:
            return np.nan

        return np.nanmean(data)

    # Appliquer la fonction à chaque point
    df['radiance_sq'] = df.apply(
        lambda row: mean_radiance_in_square(
            row['center_lon'],
            row['center_lat'],
            row['square_size_km']
        ),
        axis=1
    )

# Sauvegarde du résultat
output_file = r"D:\wealth_predict_sentinel_v2\data\output\processed_csv\coordonnees_grid_points_224km_with_radiance.csv"
df.to_csv(output_file, index=False)

print(f"Résultats enregistrés dans : {output_file}")

# 1. Chargement des données
csv_path = r'D:\wealth_predict_sentinel_v2\data\output\processed_csv\coordonnees_grid_points_224km_with_radiance.csv'
df = pd.read_csv(csv_path)

# 2. Statistiques descriptives de base
radiance = df['radiance_2240m_carre']
mean_val   = radiance.mean()
median_val = radiance.median()
std_val    = radiance.std()
quantiles  = radiance.quantile([0.25, 0.5, 0.75])

print("=== Statistiques descriptives ===")
print(f"Moyenne         : {mean_val:.4f}")
print(f"Médiane         : {median_val:.4f}")
print(f"Écart-type      : {std_val:.4f}")
print("Quantiles (25%, 50%, 75%) :")
print(quantiles.to_string())

# 3. Résumé en cinq nombres
desc = radiance.describe()
five_num = {
    'min'   : desc['min'],
    'Q1'    : desc['25%'],
    'median': desc['50%'],
    'Q3'    : desc['75%'],
    'max'   : desc['max']
}
print("\n=== Résumé en cinq nombres ===")
for k,v in five_num.items():
    print(f"{k:>6} : {v:.4f}")

# 4. Comptage des valeurs manquantes
n_missing = radiance.isna().sum()
print(f"\nNombre de valeurs manquantes dans 'radiance_2240m_carre' : {n_missing}")

# 5. Détection d’outliers par IQR
Q1 = desc['25%']
Q3 = desc['75%']
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

outliers = df[(radiance < lower_bound) | (radiance > upper_bound)]
print(f"\nNombre d'outliers détectés : {len(outliers)}")
if not outliers.empty:
    print("Exemple d'outliers (lat, lon, radiance) :")
    print(outliers[['latitude', 'longitude', 'radiance_2240m_carre']].head().to_string(index=False))

# 6. Histogramme de la distribution
plt.figure(figsize=(8,5))
plt.hist(radiance.dropna(), bins=30, edgecolor='k')
plt.title("Distribution de la radiance nocturne\n(2240 m × 2240 m)")
plt.xlabel("Radiance")
plt.ylabel("Effectif")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()

# Charger le CSV
in_path = r'D:\wealth_predict_sentinel_v2\data\output\processed_csv\coordonnees_grid_points_224km_with_radiance.csv'
df = pd.read_csv(in_path)

# Calcul du 99,9ᵉ centile
p999 = df['radiance_2240m_carre'].quantile(0.999)

# Comptage des valeurs strictement supérieures à ce centile
count_above = (df['radiance_2240m_carre'] > p999).sum()

print(f"Valeur du 99,9ᵉ centile : {p999:.4f}")
print(f"Nombre de valeurs au-dessus du 99,9ᵉ centile : {count_above}")

# Suppression des lignes dont la radiance est > 99,9ᵉ centile
df_filtered = df[df['radiance_2240m_carre'] <= p999].copy()

# (Optionnel) Afficher le nombre de lignes après filtrage
print(f"Nombre de lignes après suppression des outliers : {len(df_filtered)}")

# Sauvegarder le DataFrame filtré
out_path = r'D:\wealth_predict_sentinel_v2\data\output\processed_csv\coordonnees_grid_points_224km_with_radiance_filtered.csv'
df_filtered.to_csv(out_path, index=False)
print(f"Fichier filtré enregistré dans : {out_path}")


# modèle à 4 classes

# 1. Charger les données
def load_data(file_path):
    return pd.read_csv(file_path)

# 2. Évaluer les scores BIC
def evaluate_bic(data, column, n_components_range):
    X = data[column].values.reshape(-1, 1)
    bics, gmms = [], []
    for n in n_components_range:
        gmm = GaussianMixture(n_components=n, random_state=42)
        gmm.fit(X)
        gmms.append(gmm)
        bics.append(gmm.bic(X))
    return bics, gmms

# 3. Tracer et sauvegarder les scores BIC dynamiquement
def plot_bic(n_components_range, bics, fig_dir, n_opt):
    os.makedirs(fig_dir, exist_ok=True)
    plt.figure(figsize=(10, 6))
    plt.plot(n_components_range, bics, marker='o', linestyle='-')
    plt.title('BIC en fonction du nombre de classes', fontsize=14)
    plt.xlabel('Nombre de classes', fontsize=12)
    plt.ylabel('Score BIC', fontsize=12)
    plt.grid(True)
    fname = f"bic_gmm_{n_opt}_class.png"
    out_path = os.path.join(fig_dir, fname)
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"[✔] Graphique BIC enregistré : {out_path}")
    plt.show()

# 4. Appliquer le GMM
def apply_gmm(data, column, gmm):
    X = data[column].values.reshape(-1, 1)
    data['class'] = gmm.predict(X)
    return data

# 5. Réordonner les classes
def reorder_classes(data, gmm, column):
    class_ranges = []
    for i in range(gmm.n_components):
        vals = data.loc[data['class'] == i, column]
        class_ranges.append((i, vals.min(), vals.max(), len(vals)))
    sorted_ranges = sorted(class_ranges, key=lambda x: x[1])
    remap = {old: new for new, (old, *_ ) in enumerate(sorted_ranges)}
    data['class'] = data['class'].map(remap)
    print("\nPlages de valeurs par classe :")
    for new, (_, mn, mx, cnt) in enumerate(sorted_ranges):
        print(f"  Classe {new}: min={mn:.6f}, max={mx:.6f}, n={cnt}")
    return data

# 6. Tracer et sauvegarder l’histogramme des classes dynamiquement
def plot_histograms(data, cluster_column, fig_dir, n_opt):
    os.makedirs(fig_dir, exist_ok=True)
    plt.figure(figsize=(8, 5))
    sns.countplot(x=cluster_column, data=data)
    plt.title("Répartition des classes GMM", fontsize=14)
    plt.xlabel("Classe", fontsize=12)
    plt.ylabel("Nombre d'observations", fontsize=12)
    plt.grid(alpha=0.3)
    fname = f"hist_classes_{n_opt}_class.png"
    out_path = os.path.join(fig_dir, fname)
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"[✔] Histogramme des classes enregistré : {out_path}")
    plt.show()

# 7. Fonction principale
def main(
    file_path,
    output_path,
    fig_dir,
    column='radiance_2240m_carre',
    n_components_range=range(1, 5)
):
    # Chargement
    df = load_data(file_path)

    # Évaluation BIC
    bics, gmms = evaluate_bic(df, column, n_components_range)

    # Sélection du nombre optimal de classes
    idx = np.argmin(bics)
    n_opt = n_components_range[idx]
    print(f"\nNombre optimal de classes selon BIC : {n_opt}")

    # Sauvegarde dynamique du graphique BIC
    plot_bic(n_components_range, bics, fig_dir, n_opt)

    # Application du GMM optimal
    gmm = gmms[idx]
    df = apply_gmm(df, column, gmm)

    # Réordonnancement et histogramme
    df = reorder_classes(df, gmm, column)
    plot_histograms(df, 'class', fig_dir, n_opt)

    # Nom de sortie CSV dynamique
    root, ext = os.path.splitext(output_path)
    dynamic_csv = f"{root}_{n_opt}_class{ext}"
    df.to_csv(dynamic_csv, index=False)
    print(f"[✔] Données classées sauvegardées : {dynamic_csv}")

    return df

if __name__ == "__main__":
    inp     = r"D:\wealth_predict_sentinel_v2\data\output\processed_csv\coordonnees_grid_points_224km_with_radiance_filtered.csv"
    out     = r"D:\wealth_predict_sentinel_v2\data\output\processed_csv\coordonnees_grid_points_224km_with_radiance_classified.csv"
    figures = r"D:\wealth_predict_sentinel_v2\figures_graphs"

    df_final = main(inp, out, figures)


# Modèle à 3 classes

# 1. Charger les données
def load_data(file_path):
    return pd.read_csv(file_path)

# 2. Évaluer les scores BIC
def evaluate_bic(data, column, n_components_range):
    X = data[column].values.reshape(-1, 1)
    bics, gmms = [], []
    for n in n_components_range:
        gmm = GaussianMixture(n_components=n, random_state=42)
        gmm.fit(X)
        gmms.append(gmm)
        bics.append(gmm.bic(X))
    return bics, gmms

# 3. Tracer et sauvegarder les scores BIC dynamiquement
def plot_bic(n_components_range, bics, fig_dir, n_opt):
    os.makedirs(fig_dir, exist_ok=True)
    plt.figure(figsize=(10, 6))
    plt.plot(n_components_range, bics, marker='o', linestyle='-')
    plt.title('BIC en fonction du nombre de classes', fontsize=14)
    plt.xlabel('Nombre de classes', fontsize=12)
    plt.ylabel('Score BIC', fontsize=12)
    plt.grid(True)
    fname = f"bic_gmm_{n_opt}_class.png"
    out_path = os.path.join(fig_dir, fname)
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"[✔] Graphique BIC enregistré : {out_path}")
    plt.show()

# 4. Appliquer le GMM
def apply_gmm(data, column, gmm):
    X = data[column].values.reshape(-1, 1)
    data['class'] = gmm.predict(X)
    return data

# 5. Réordonner les classes
def reorder_classes(data, gmm, column):
    class_ranges = []
    for i in range(gmm.n_components):
        vals = data.loc[data['class'] == i, column]
        class_ranges.append((i, vals.min(), vals.max(), len(vals)))
    sorted_ranges = sorted(class_ranges, key=lambda x: x[1])
    remap = {old: new for new, (old, *_ ) in enumerate(sorted_ranges)}
    data['class'] = data['class'].map(remap)
    print("\nPlages de valeurs par classe :")
    for new, (_, mn, mx, cnt) in enumerate(sorted_ranges):
        print(f"  Classe {new}: min={mn:.6f}, max={mx:.6f}, n={cnt}")
    return data

# 6. Tracer et sauvegarder l’histogramme des classes dynamiquement
def plot_histograms(data, cluster_column, fig_dir, n_opt):
    os.makedirs(fig_dir, exist_ok=True)
    plt.figure(figsize=(8, 5))
    sns.countplot(x=cluster_column, data=data)
    plt.title("Répartition des classes GMM", fontsize=14)
    plt.xlabel("Classe", fontsize=12)
    plt.ylabel("Nombre d'observations", fontsize=12)
    plt.grid(alpha=0.3)
    fname = f"hist_classes_{n_opt}_class.png"
    out_path = os.path.join(fig_dir, fname)
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"[✔] Histogramme des classes enregistré : {out_path}")
    plt.show()

# 7. Fonction principale
def main(
    file_path,
    output_path,
    fig_dir,
    column='radiance_2240m_carre',
    n_components_range=range(1, 4)
):
    # Chargement
    df = load_data(file_path)

    # Évaluation BIC
    bics, gmms = evaluate_bic(df, column, n_components_range)

    # Sélection du nombre optimal de classes
    idx = np.argmin(bics)
    n_opt = n_components_range[idx]
    print(f"\nNombre optimal de classes selon BIC : {n_opt}")

    # Sauvegarde dynamique du graphique BIC
    plot_bic(n_components_range, bics, fig_dir, n_opt)

    # Application du GMM optimal
    gmm = gmms[idx]
    df = apply_gmm(df, column, gmm)

    # Réordonnancement et histogramme
    df = reorder_classes(df, gmm, column)
    plot_histograms(df, 'class', fig_dir, n_opt)

    # Nom de sortie CSV dynamique
    root, ext = os.path.splitext(output_path)
    dynamic_csv = f"{root}_{n_opt}_class{ext}"
    df.to_csv(dynamic_csv, index=False)
    print(f"[✔] Données classées sauvegardées : {dynamic_csv}")

    return df

if __name__ == "__main__":
    inp     = r"D:\wealth_predict_sentinel_v2\data\output\processed_csv\coordonnees_grid_points_224km_with_radiance_filtered.csv"
    out     = r"D:\wealth_predict_sentinel_v2\data\output\processed_csv\coordonnees_grid_points_224km_with_radiance_classified.csv"
    figures = r"D:\wealth_predict_sentinel_v2\figures_graphs"

    df_final = main(inp, out, figures)


# Réglages
seed = 42
pd.options.mode.chained_assignment = None  # désactiver les warnings de copie de pandas

def balanced_sample(input_csv):
    """
    Charge un CSV classifié, effectue un échantillonnage équilibré par classe,
    et sauve le DataFrame résultant dans un fichier dont le nom reflète
    le nombre de classes.
    """
    # Charger les données
    df = pd.read_csv(input_csv)
    
    # Nombre de classes
    classes = sorted(df['class'].unique())
    n_classes = len(classes)
    
    # Calcul de la taille minimale parmi les classes
    counts = df['class'].value_counts()
    min_count = counts.min()
    print(f"Classes trouvées : {classes}")
    print(f"Effectifs par classe :\n{counts.to_string()}")
    print(f"Taille de l'échantillon par classe : {min_count}\n")
    
    # Échantillonnage équilibré
    sampled_parts = []
    for cls in classes:
        part = df[df['class'] == cls].sample(n=min_count, random_state=seed)
        sampled_parts.append(part)
    
    df_balanced = pd.concat(sampled_parts, ignore_index=True)
    
    # Vérification
    print("Effectifs après échantillonnage :")
    print(df_balanced['class'].value_counts().sort_index().to_string())
    print("\nAperçu des données équilibrées :")
    print(df_balanced.head(10).to_string(index=False))
    
    # Construction du chemin de sortie dynamique
    base, ext = os.path.splitext(input_csv)
    out_csv = f"{base}_balanced_{n_classes}_class{ext}"
    
    # Sauvegarde
    df_balanced.to_csv(out_csv, index=False)
    print(f"\n[✔] Échantillon équilibré enregistré dans : {out_csv}")
    
    return df_balanced

if __name__ == "__main__":
    # Exemples d'utilisation
    path_4 = r"D:\wealth_predict_sentinel_v2\data\output\processed_csv\coordonnees_grid_points_224km_with_radiance_classified_4_class.csv"
    path_3 = r"D:\wealth_predict_sentinel_v2\data\output\processed_csv\coordonnees_grid_points_224km_with_radiance_classified_3_class.csv"
    
    # Pour le modèle à 4 classes
    balanced_4 = balanced_sample(path_4)
    
    # Pour le modèle à 3 classes
    balanced_3 = balanced_sample(path_3)



# Chemins et fichiers à traiter
datasets = {
    "4_class": r"D:\wealth_predict_sentinel_v2\data\output\processed_csv\coordonnees_grid_points_224km_with_radiance_classified_4_class_balanced_4_class.csv",
    "3_class": r"D:\wealth_predict_sentinel_v2\data\output\processed_csv\coordonnees_grid_points_224km_with_radiance_classified_3_class_balanced_3_class.csv"
}

geojson_path = r"D:\wealth_predict_sentinel_v2\data\downloaded\africa.json"
figures_output_dir = r"D:\wealth_predict_sentinel_v2\figures_graphs"

# Créer le dossier de sortie s'il n'existe pas
os.makedirs(figures_output_dir, exist_ok=True)

# Charger les frontières de l'Afrique
print("Chargement des frontières de l'Afrique depuis le GeoJSON...")
africa = gpd.read_file(geojson_path)

for tag, csv_path in datasets.items():
    print(f"\n--- Génération de la carte de chaleur pour le jeu '{tag}' ---")
    
    # Charger les données
    df = pd.read_csv(csv_path)
    
    # Vérifier que les colonnes attendues sont présentes
    required = {'longitude', 'latitude', 'radiance_2240m_carre'}
    if not required.issubset(df.columns):
        raise ValueError(f"Le fichier {csv_path} doit contenir les colonnes {required}")
    
    # Création de la figure
    fig, ax = plt.subplots(figsize=(12, 12))
    
    # Tracer les frontières
    africa.plot(ax=ax, color='lightgrey', edgecolor='black')
    
    # Scatter des points colorés par radiance
    sc = ax.scatter(
        df['longitude'],
        df['latitude'],
        c=df['radiance_2240m_carre'],
        cmap='inferno',
        alpha=0.7,
        s=15,
        linewidth=0
    )
    
    # Barre de couleur
    cbar = plt.colorbar(sc, ax=ax, fraction=0.03, pad=0.04)
    cbar.set_label('Radiance (2240m × 2240m)', fontsize=12)
    
    # Titres et étiquettes
    ax.set_title(f"Carte de Chaleur de la Radiance Nocturne — {tag.replace('_', ' ')}", fontsize=16)
    ax.set_xlabel('Longitude', fontsize=12)
    ax.set_ylabel('Latitude', fontsize=12)
    
    # Enregistrer la figure
    out_png = os.path.join(figures_output_dir, f"heatmap_radiance_{tag}.png")
    plt.savefig(out_png, dpi=300, bbox_inches='tight')
    print(f"[✔] Carte sauvegardée : {out_png}")
    
    plt.show(fig)  # Fermer la figure pour libérer la mémoire

print("\nToutes les cartes de chaleur ont été générées avec succès.")
