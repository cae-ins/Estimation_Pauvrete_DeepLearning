
import pandas as pd
import os
import glob

# Chemin vers le dossier contenant les fichiers CSV
dossier_csv = r"D:\wealth_predict_sentinel_v2\data\output\processed_csv"

# Liste pour stocker tous les DataFrames
dataframes_list = []

# Parcourir tous les fichiers CSV dans le dossier
fichiers_csv = glob.glob(os.path.join(dossier_csv, "*.csv"))

print(f"Fichiers trouvés : {len(fichiers_csv)}")
for fichier in fichiers_csv:
    print(f"- {os.path.basename(fichier)}")

print("\nTraitement des fichiers...")

# Traiter chaque fichier CSV
for fichier in fichiers_csv:
    nom_fichier = os.path.basename(fichier)
    print(f"\nTraitement de : {nom_fichier}")
    
    try:
        # Lire le fichier CSV
        df = pd.read_csv(fichier)
        
        print(f"  Colonnes détectées : {list(df.columns)}")
        print(f"  Nombre de lignes : {len(df)}")
        
        # Vérifier que les colonnes latitude et longitude existent
        if 'latitude' in df.columns and 'longitude' in df.columns:
            # Extraire seulement les colonnes latitude et longitude
            df_coords = df[['latitude', 'longitude']].copy()
            
            # Supprimer les lignes avec des valeurs manquantes
            df_coords = df_coords.dropna()
            
            # Ajouter le nom du fichier pour traçabilité (optionnel)
            df_coords['source'] = nom_fichier
            
            dataframes_list.append(df_coords)
            print(f"  ✓ {len(df_coords)} coordonnées extraites")
        else:
            print(f"  ✗ Colonnes latitude/longitude manquantes dans {nom_fichier}")
            
    except Exception as e:
        print(f"  ✗ Erreur lors du traitement de {nom_fichier}: {str(e)}")

# Combiner tous les DataFrames
if dataframes_list:
    print(f"\nCombiner {len(dataframes_list)} fichiers...")
    df_combined = pd.concat(dataframes_list, ignore_index=True)
    
    print(f"Total des lignes avant suppression des doublons : {len(df_combined)}")
    
    # Supprimer les doublons basés sur latitude et longitude
    # On arrondit à 6 décimales pour éviter les micro-différences
    df_combined['lat_rounded'] = df_combined['latitude'].round(6)
    df_combined['lon_rounded'] = df_combined['longitude'].round(6)
    
    # Supprimer les doublons
    df_final = df_combined.drop_duplicates(subset=['lat_rounded', 'lon_rounded'])
    
    # Garder seulement les colonnes originales latitude et longitude
    df_final = df_final[['latitude', 'longitude']].copy()
    
    print(f"Total des lignes après suppression des doublons : {len(df_final)}")
    print(f"Doublons supprimés : {len(df_combined) - len(df_final)}")
    
    # Afficher quelques statistiques
    print(f"\nStatistiques des coordonnées :")
    print(f"Latitude min : {df_final['latitude'].min():.6f}")
    print(f"Latitude max : {df_final['latitude'].max():.6f}")
    print(f"Longitude min : {df_final['longitude'].min():.6f}")
    print(f"Longitude max : {df_final['longitude'].max():.6f}")
    
    # Sauvegarder le résultat
    fichier_sortie = os.path.join(dossier_csv, "df_afrique_coordonnees_consolidees.csv")
    df_final.to_csv(fichier_sortie, index=False)
    print(f"\n✓ Fichier consolidé sauvegardé : {fichier_sortie}")
    
    # Afficher les premières lignes
    print(f"\nPremières lignes du fichier consolidé :")
    print(df_final.head(10))
    
else:
    print("Aucun fichier n'a pu être traité avec succès.")
    
print("\nScript terminé !")