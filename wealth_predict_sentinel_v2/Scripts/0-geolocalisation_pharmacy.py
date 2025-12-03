'''
Pharmacies a Abidjan dans une grille de 17.82 km x 17.80 km de cote,
avec 100 zones, et chaque point formant ces zones est espace d'environ 2 km
et cette grille est centree sur un point GPS Central d'Abidjan**
##### **(lat_center = 5.354444, lon_center = -3.998889)**
'''
'''
get_pharmacies()
Cette fonction envoie une requête à l'API Google Places pour récupérer les pharmacies dans une zone définie par un point central (location) et un rayon de recherche (radius).
- API Google Places : Cette API renvoie les lieux correspondant à la recherche (ici les pharmacies) dans un rayon de 1000 mètres autour du point central (location).
- Pagination : Si l'API renvoie plus de 20 résultats, un next_page_token est utilisé pour récupérer les pages suivantes.
- Résultats : Les résultats incluent le nom, la latitude, et la longitude de chaque pharmacie.
'''
'''
generate_zones()
Cette fonction génère une grille de points centraux répartis sur une zone, selon des intervalles de latitude et de longitude (lat_step, lon_step).
- num_lat et num_lon : Représentent le nombre de zones en latitude et en longitude.
- lat_step et lon_step : Définissent l'espacement entre chaque zone en degrés. Cela permet de générer une grille de points centraux autour d'un point de référence. (1 degré = 111 km)
'''

import requests
import pandas as pd
import time



def get_pharmacies(api_key, location, radius=1000, query="pharmacy"):
    """
    Récupère les pharmacies pour une zone donnée avec gestion de la pagination.

    :param api_key: Votre clé API Google.
    :param location: Coordonnées GPS du centre de la zone (latitude, longitude).
    :param radius: Rayon de recherche en mètres.
    :param query: Type de lieu à rechercher ("pharmacy").
    :return: Une liste de dictionnaires avec les noms et coordonnées des pharmacies.
    """
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        'query': query,
        'location': location,
        'radius': radius,
        'key': api_key
    }

    all_pharmacies = []

    while True:
        # Envoie la requête HTTP à l'API Google Places
        response = requests.get(url, params=params)
        # Récupère les résultats sous forme JSON
        results = response.json().get('results', [])
        # Ajoute chaque pharmacie à la liste 'all_pharmacies'
        all_pharmacies.extend([{
            'name': place.get('name'),
            'latitude': place['geometry']['location']['lat'],
            'longitude': place['geometry']['location']['lng']
        } for place in results])

        # Vérifie s'il y a une page suivante de résultats
        next_page_token = response.json().get('next_page_token')
        if not next_page_token:
            break

        # Attends quelques secondes avant de récupérer la page suivante
        time.sleep(2)
        params['pagetoken'] = next_page_token

    return all_pharmacies

def generate_zones(lat_center, lon_center, lat_step, lon_step, num_lat, num_lon):
    """
    Génère une grille de coordonnées pour découper la ville en zones de recherche plus petites.

    :param lat_center: Latitude centrale de la ville.
    :param lon_center: Longitude centrale de la ville.
    :param lat_step: Pas en latitude pour chaque sous-zone.
    :param lon_step: Pas en longitude pour chaque sous-zone.
    :param num_lat: Nombre de zones en latitude.
    :param num_lon: Nombre de zones en longitude.
    :return: Une liste de coordonnées GPS pour le centre de chaque sous-zone.
    """
    zones = []
    for i in range(num_lat):
        for j in range(num_lon):
            # Calcul de la latitude et longitude du point central de chaque zone
            lat = lat_center + (i - num_lat // 2) * lat_step
            lon = lon_center + (j - num_lon // 2) * lon_step
            zones.append(f"{lat},{lon}")
    return zones

# Liste pour stocker toutes les pharmacies
all_pharmacies = []

# Recherche dans chaque sous-zone
for zone in zones:
    print(f"Recherche dans la zone : {zone}")
    pharmacies = get_pharmacies(api_key=API_KEY, location=zone, radius=1000)
    all_pharmacies.extend(pharmacies)

# Création du DataFrame à partir des pharmacies trouvées
df_pharmacies = pd.DataFrame(all_pharmacies)

# Affichage du nombre total de pharmacies avant suppression des doublons
print(f"Nombre total de pharmacies avant suppression des doublons : {len(df_pharmacies)}")

# Détection et suppression des doublons basés sur les colonnes 'name', 'latitude', et 'longitude'
duplicates = df_pharmacies[df_pharmacies.duplicated(subset=['name', 'latitude', 'longitude'], keep=False)]
print(f"Nombre de doublons trouvés : {duplicates.shape[0]}")

# Suppression des doublons (en gardant la première occurrence)
df_pharmacies_unique = df_pharmacies.drop_duplicates(subset=['name', 'latitude', 'longitude'])

# Affichage du nombre de pharmacies après suppression des doublons
print(f"Nombre de pharmacies après suppression des doublons : {len(df_pharmacies_unique)}")

# Ajout de la colonne 'country' avec la valeur 'CIV' pour chaque ligne
df_pharmacies_unique['country'] = 'CIV'

# Sauvegarde du fichier CSV
csv_filename = "pharmacies_abidjan_complet_sans_doublons.csv"
df_pharmacies_unique.to_csv(csv_filename, index=False)

# Téléchargement du fichier CSV sur votre machine locale
files.download(csv_filename)

#visualisation
import folium

def generate_zones(lat_center, lon_center, lat_step, lon_step, num_lat, num_lon):
    """
    Génère une grille de coordonnées pour découper la ville en zones de recherche plus petites.

    :param lat_center: Latitude centrale de la ville.
    :param lon_center: Longitude centrale de la ville.
    :param lat_step: Pas en latitude pour chaque sous-zone.
    :param lon_step: Pas en longitude pour chaque sous-zone.
    :param num_lat: Nombre de zones en latitude.
    :param num_lon: Nombre de zones en longitude.
    :return: Une liste de coordonnées GPS pour le centre de chaque sous-zone.
    """
    zones = []
    for i in range(num_lat):
        for j in range(num_lon):
            lat = lat_center + (i - num_lat // 2) * lat_step
            lon = lon_center + (j - num_lon // 2) * lon_step
            zones.append((lat, lon))
    return zones

# Coordonnées centrales d'Abidjan
lat_center = 5.354444
lon_center = -3.998889

# Paramètres de la grille (pour une distance de  km)
lat_step = 0.018  # environ 2 km en latitude
lon_step = 0.018  # environ 2 km en longitude
num_lat = 10     #10 zones en latitude
num_lon = 10     # 10 zones en longitude

# Génération des sous-zones (400 zones au total)
zones = generate_zones(lat_center, lon_center, lat_step, lon_step, num_lat, num_lon)

# Créer une carte centrée sur Abidjan
map_abidjan = folium.Map(location=[lat_center, lon_center], zoom_start=12)

# Ajouter les points centraux à la carte
for zone in zones:
    folium.Marker(location=zone, popup=f"Lat: {zone[0]}, Lon: {zone[1]}").add_to(map_abidjan)

# Afficher la carte
map_abidjan

df_pharmacies_unique

'''
Pharmacie à Bouaké
'''
import requests
import pandas as pd
import time
import folium
from selenium import webdriver
from pyvirtualdisplay import Display
from google.colab import files

# Fonction pour récupérer les pharmacies
def get_pharmacies(api_key, location, radius=1000, query="pharmacy"):
    """
    Récupère les pharmacies pour une zone donnée avec gestion de la pagination.
    """
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        'query': query,
        'location': location,
        'radius': radius,
        'key': api_key
    }

    all_pharmacies = []

    while True:
        response = requests.get(url, params=params)
        results = response.json().get('results', [])
        all_pharmacies.extend([{
            'name': place.get('name'),
            'latitude': place['geometry']['location']['lat'],
            'longitude': place['geometry']['location']['lng']
        } for place in results])

        next_page_token = response.json().get('next_page_token')
        if not next_page_token:
            break

        time.sleep(2)
        params['pagetoken'] = next_page_token

    return all_pharmacies

# Fonction pour générer les zones
def generate_zones(lat_center, lon_center, lat_step, lon_step, num_lat, num_lon):
    """
    Génère une grille de coordonnées pour découper la ville en zones de recherche plus petites.
    """
    zones = []
    for i in range(num_lat):
        for j in range(num_lon):
            lat = lat_center + (i - num_lat // 2) * lat_step
            lon = lon_center + (j - num_lon // 2) * lon_step
            zones.append((lat, lon))  # Retourner des tuples (lat, lon) pour folium
    return zones

# Clé API Google (remplacer par la vôtre)
API_KEY = " "# Clé API Google

# Coordonnées centrales de Bouaké
lat_center = 7.693849
lon_center = -5.030305

# Paramètres de la grille pour couvrir une distance de 2 km en latitude et longitude
lat_step = 0.018  # Environ 2 km en latitude
lon_step = 0.018  # Environ 2 km en longitude
num_lat = 10      # 10 zones en latitude
num_lon = 10      # 10 zones en longitude

# Génération des sous-zones (100 zones au total)
zones = generate_zones(lat_center, lon_center, lat_step, lon_step, num_lat, num_lon)

# Liste pour stocker toutes les pharmacies
all_pharmacies = []

# Recherche dans chaque sous-zone
for zone in zones:
    print(f"Recherche dans la zone : {zone}")
    pharmacies = get_pharmacies(api_key=API_KEY, location=f"{zone[0]},{zone[1]}", radius=1000)
    all_pharmacies.extend(pharmacies)

# Création du DataFrame à partir des pharmacies trouvées
df_pharmacies = pd.DataFrame(all_pharmacies)

# Affichage du nombre total de pharmacies avant suppression des doublons
print(f"Nombre total de pharmacies avant suppression des doublons : {len(df_pharmacies)}")

# Détection et suppression des doublons basés sur les colonnes 'name', 'latitude', et 'longitude'
duplicates = df_pharmacies[df_pharmacies.duplicated(subset=['name', 'latitude', 'longitude'], keep=False)]
print(f"Nombre de doublons trouvés : {duplicates.shape[0]}")

# Suppression des doublons (en gardant la première occurrence)
df_pharmacies_unique = df_pharmacies.drop_duplicates(subset=['name', 'latitude', 'longitude'])

# Affichage du nombre de pharmacies après suppression des doublons
print(f"Nombre de pharmacies après suppression des doublons : {len(df_pharmacies_unique)}")

# Ajout de la colonne 'country' avec la valeur 'CIV' pour chaque ligne
df_pharmacies_unique['country'] = 'CIV'

# Sauvegarde du fichier CSV
csv_filename = "pharmacies_bouake_complet_sans_doublons.csv"
df_pharmacies_unique.to_csv(csv_filename, index=False)

# Téléchargement du fichier CSV sur votre machine locale
files.download(csv_filename)

# Créer une carte centrée sur Bouaké
map_bouake = folium.Map(location=[lat_center, lon_center], zoom_start=12)

# Ajouter les points centraux à la carte
for zone in zones:
    folium.Marker(location=zone, popup=f"Lat: {zone[0]}, Lon: {zone[1]}").add_to(map_bouake)

# Sauvegarder la carte en fichier HTML
html_filename = "map_bouake.html"
map_bouake.save(html_filename)

# Utiliser pyvirtualdisplay pour démarrer un affichage virtuel
display = Display(visible=0, size=(800, 600))
display.start()

# Configurer le navigateur Firefox en mode headless
options = webdriver.FirefoxOptions()
options.add_argument("--headless")

# Lancer le navigateur avec Selenium
driver = webdriver.Firefox(options=options)

# Charger le fichier HTML de la carte
driver.get(f"file:///content/{html_filename}")

# Attendre quelques secondes pour que la carte soit complètement chargée
time.sleep(5)

# Capturer une capture d'écran de la carte
screenshot_filename = "map_bouake.png"
driver.save_screenshot(screenshot_filename)

# Fermer le navigateur et arrêter l'affichage virtuel
driver.quit()
display.stop()

# Télécharger l'image de la carte
files.download(screenshot_filename)

'''
Pharmacie à Yamoussoukro
'''
# Fonction pour récupérer les pharmacies
def get_pharmacies(api_key, location, radius=1000, query="pharmacy"):
    """
    Récupère les pharmacies pour une zone donnée avec gestion de la pagination.
    """
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        'query': query,
        'location': location,
        'radius': radius,
        'key': api_key
    }

    all_pharmacies = []

    while True:
        # Envoie la requête HTTP à l'API Google Places
        response = requests.get(url, params=params)
        # Récupère les résultats sous forme JSON
        results = response.json().get('results', [])
        # Ajoute chaque pharmacie à la liste 'all_pharmacies'
        all_pharmacies.extend([{
            'name': place.get('name'),
            'latitude': place['geometry']['location']['lat'],
            'longitude': place['geometry']['location']['lng']
        } for place in results])

        # Vérifie s'il y a une page suivante de résultats
        next_page_token = response.json().get('next_page_token')
        if not next_page_token:
            break

        # Attends quelques secondes avant de récupérer la page suivante
        time.sleep(2)
        params['pagetoken'] = next_page_token

    return all_pharmacies

# Fonction pour générer les zones
def generate_zones(lat_center, lon_center, lat_step, lon_step, num_lat, num_lon):
    """
    Génère une grille de coordonnées pour découper la ville en zones de recherche plus petites.
    """
    zones = []
    for i in range(num_lat):
        for j in range(num_lon):
            # Retourner des tuples (latitude, longitude) au lieu de strings
            lat = lat_center + (i - num_lat // 2) * lat_step
            lon = lon_center + (j - num_lon // 2) * lon_step
            zones.append((lat, lon))  # Append as tuple (lat, lon)
    return zones

# Clé API Google 
API_KEY = " " #Mettre sa clé API ici entre les "" 

# Coordonnées centrales de Yamoussoukro
lat_center = 6.8214
lon_center = -5.276

# Paramètres de la grille pour couvrir une distance de 2 km en latitude et longitude
lat_step = 0.018  # Environ 2 km en latitude
lon_step = 0.018  # Environ 2 km en longitude
num_lat = 10      # 10 zones en latitude
num_lon = 10      # 10 zones en longitude

# Génération des sous-zones (100 zones au total)
zones = generate_zones(lat_center, lon_center, lat_step, lon_step, num_lat, num_lon)

# Liste pour stocker toutes les pharmacies
all_pharmacies = []

# Recherche dans chaque sous-zone
for zone in zones:
    print(f"Recherche dans la zone : {zone}")
    pharmacies = get_pharmacies(api_key=API_KEY, location=f"{zone[0]},{zone[1]}", radius=1000)
    all_pharmacies.extend(pharmacies)

# Création du DataFrame à partir des pharmacies trouvées
df_pharmacies = pd.DataFrame(all_pharmacies)

# Affichage du nombre total de pharmacies avant suppression des doublons
print(f"Nombre total de pharmacies avant suppression des doublons : {len(df_pharmacies)}")

# Détection et suppression des doublons
df_pharmacies_unique = df_pharmacies.drop_duplicates(subset=['name', 'latitude', 'longitude'])

# Affichage du nombre de pharmacies après suppression des doublons
print(f"Nombre de pharmacies après suppression des doublons : {len(df_pharmacies_unique)}")

# Ajout de la colonne 'country' avec la valeur 'CIV' pour chaque ligne
df_pharmacies_unique['country'] = 'CIV'

# Sauvegarde du fichier CSV
csv_filename = "pharmacies_yamoussoukro_complet_sans_doublons.csv"
df_pharmacies_unique.to_csv(csv_filename, index=False)

# Téléchargement du fichier CSV sur votre machine locale
files.download(csv_filename)

# Créer une carte centrée sur Yamoussoukro
map_yamoussoukro = folium.Map(location=[lat_center, lon_center], zoom_start=12)

# Ajouter les points centraux à la carte
for zone in zones:
    folium.Marker(location=zone, popup=f"Lat: {zone[0]}, Lon: {zone[1]}").add_to(map_yamoussoukro)

# Sauvegarder la carte en fichier HTML
map_yamoussoukro.save("map_yamoussoukro.html")

# Utiliser pyvirtualdisplay pour démarrer un affichage virtuel
display = Display(visible=0, size=(800, 600))
display.start()

# Configurer le navigateur Firefox en mode headless
options = webdriver.FirefoxOptions()
options.add_argument("--headless")

# Lancer le navigateur avec Selenium
driver = webdriver.Firefox(options=options)

# Charger le fichier HTML de la carte
driver.get("file:///content/map_yamoussoukro.html")

# Attendre quelques secondes pour que la carte soit complètement chargée
time.sleep(5)

# Capturer une capture d'écran de la carte
driver.save_screenshot("map_yamoussoukro.png")

# Fermer le navigateur et arrêter l'affichage virtuel
driver.quit()
display.stop()

# Télécharger l'image de la carte
files.download("map_yamoussoukro.png")


'''
Pharmacie aux pays de l'Afrique - Utilisation de Open Street Maps - API Overpass
'''
# Fonction pour interroger l'API Overpass et obtenir les pharmacies dans une zone donnée
def get_pharmacies_osm(latitude, longitude, radius=1000):
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    (
      node["amenity"="pharmacy"](around:{radius},{latitude},{longitude});
    );
    out body;
    """
    response = requests.get(overpass_url, params={'data': overpass_query})

    if response.status_code != 200:
        raise Exception(f"Erreur lors de la requête Overpass : {response.status_code}")

    data = response.json()

    # Extraire les informations des pharmacies (nom, latitude, longitude)
    pharmacies = []
    for element in data['elements']:
        if 'tags' in element and 'name' in element['tags']:
            pharmacies.append({
                'name': element['tags']['name'],
                'latitude': element['lat'],
                'longitude': element['lon']
            })

    return pharmacies

# Fonction pour générer une grille de points autour d'un centre
def generate_zones(lat_center, lon_center, lat_step, lon_step, num_lat, num_lon):
    zones = []
    for i in range(num_lat):
        for j in range(num_lon):
            lat = lat_center + (i - num_lat // 2) * lat_step
            lon = lon_center + (j - num_lon // 2) * lon_step
            zones.append((lat, lon))
    return zones

# Fonction pour télécharger une image de la carte générée avec folium
def capture_map(map_object, filename):
    # Démarrer un affichage virtuel avec pyvirtualdisplay
    display = Display(visible=0, size=(800, 600))
    display.start()

    # Utiliser Selenium pour ouvrir Firefox et capturer la carte
    map_object.save('map.html')
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)

    # Charger le fichier HTML
    driver.get("file:///content/map.html")

    # Attendre que la carte se charge
    time.sleep(5)

    # Capturer une capture d'écran de la carte
    driver.save_screenshot(filename)

    # Fermer le navigateur et arrêter l'affichage virtuel
    driver.quit()
    display.stop()

    print(f"Carte sauvegardée sous : {filename}")

# Dictionnaire des villes Africaine et leurs coordonnées (latitude, longitude)
#Ghana, Benin, Burkina,Cameroun, Gabon, Guinee, Kenya, Liberia, Mali
#Nigeria, Ouganda, Rwanda, Senegal, Togo, Sierra Leone
#Ethiopie, Congo Brazzaville, Congo Kinshasa, Tchad et Niger
#20 pays et 630 villes

cities_coordinates ={
    "Accra": (5.6037, -0.1870),
    "Kumasi": (6.6886, -1.6244),
    "Tamale": (9.4071, -0.8539),
    "Sekondi-Takoradi": (4.9341, -1.7040),
    "Ashaiman": (5.6986, -0.0286),
    "Sunyani": (7.3399, -2.3268),
    "Cape Coast": (5.1054, -1.2466),
    "Obuasi": (6.2023, -1.6676),
    "Teshie": (5.5830, -0.1000),
    "Tema": (5.6697, 0.0166),
    "Ho": (6.6117, 0.4781),
    "Wa": (10.0607, -2.5019),
    "Bolgatanga": (10.7850, -0.8514),
    "Bawku": (11.0615, -0.2417),
    "Koforidua": (6.0941, -0.2591),
    "Techiman": (7.5862, -1.9357),
    "Suhum": (6.0385, -0.4507),
    "Nkawkaw": (6.5534, -0.7644),
    "Winneba": (5.3517, -0.6230),
    "Agona Swedru": (5.5187, -0.6998),
    "Savelugu": (9.6244, -0.8296),
    "Konongo": (6.6161, -1.2120),
    "Nsawam": (5.8072, -0.3529),
    "Mampong": (7.0621, -1.4041),
    "Berekum": (7.4519, -2.5843),
    "Navrongo": (10.8956, -1.0921),
    "Gbawe": (5.5831, -0.3106),
    "Axim": (4.8669, -2.2366),
    "Elmina": (5.0852, -1.3495),
    "Anloga": (5.7946, 0.8975),
    "Begoro": (6.3873, -0.3799),
    "Tarkwa": (5.3075, -1.9855),
    "Salaga": (8.5500, -0.5183),
    "Shama": (5.0017, -1.6316),
    "Bechem": (7.0904, -2.0246),
    "Ejura": (7.3849, -1.3566),
    "Akim Oda": (5.9279, -0.9847),
    "Wenchi": (7.7395, -2.1041),
    "Nalerigu": (10.5260, -0.3665),
    "Akosombo": (6.2961, 0.0637),
    "Asamankese": (5.8607, -0.6659),
    "Kintampo": (8.0556, -1.7304),
    "Somanya": (6.1337, -0.0025),
    "Zebilla": (10.9526, -0.6351),
    "Kpandu": (7.0084, 0.3002),
    "Atebubu": (7.7539, -0.9427),
    "Foso": (5.7076, -1.2863),
    "Mpraeso": (6.5879, -0.7257),
    "Cotonou": (6.3654, 2.4183),
    "Porto-Novo": (6.4969, 2.6289),
    "Parakou": (9.3467, 2.6099),
    "Abomey-Calavi": (6.4483, 2.3557),
    "Djougou": (9.7085, 1.6657),
    "Bohicon": (7.1787, 2.0658),
    "Natitingou": (10.2983, 1.3793),
    "Abomey": (7.1824, 1.9912),
    "Kandi": (11.1342, 2.9383),
    "Ouidah": (6.3655, 2.0852),
    "Savalou": (7.9283, 1.9751),
    "Lokossa": (6.6383, 1.7167),
    "Malanville": (11.8654, 3.3854),
    "Pobè": (6.9808, 2.6649),
    "Sakété": (6.7426, 2.6589),
    "Covè": (7.2204, 2.3405),
    "Kérou": (10.8181, 1.9458),
    "Banikoara": (11.3003, 2.4389),
    "Bassila": (9.0118, 1.6654),
    "Allada": (6.6623, 2.1511),
    "Tanguiéta": (10.6193, 1.2657),
    "Dogbo-Tota": (6.8054, 1.7779),
    "Dassa-Zoumé": (7.7483, 2.1836),
    "Comè": (6.4076, 1.8819),
    "Bembèrèkè": (10.2284, 2.6637),
    "Nikki": (9.9401, 3.2073),
    "Tchaourou": (8.8866, 2.5971),
    "Aplahoué": (6.9339, 1.6742),
    "Grand-Popo": (6.2836, 1.8188),
    "Djakotomey": (6.8797, 1.7048),
    "Zangnanado": (7.2484, 2.4299),
    "Cové": (7.2254, 2.3425),
    "Zè": (6.5115, 2.1061),
    "Toucountouna": (10.6217, 1.4081),
    "Materi": (10.6883, 1.4012),
    "Segbana": (10.9643, 3.7423),
    "Kpomassè": (6.4727, 2.0764),
    "Athiémè": (6.5967, 1.7219),
    "Ouagadougou": (12.3714, -1.5197),
    "Bobo-Dioulasso": (11.1771, -4.2979),
    "Koudougou": (12.2513, -2.3627),
    "Banfora": (10.6333, -4.7667),
    "Ouahigouya": (13.5703, -2.4216),
    "Fada N'Gourma": (12.0615, 0.3589),
    "Tenkodogo": (11.7833, -0.3697),
    "Dori": (14.0357, -0.0328),
    "Houndé": (11.5000, -3.5167),
    "Gaoua": (10.3167, -3.1833),
    "Manga": (11.6641, -1.0732),
    "Ziniaré": (12.5833, -1.3000),
    "Po": (11.1696, -1.1475),
    "Kaya": (13.0917, -1.0844),
    "Boussé": (12.6619, -1.8917),
    "Reo": (12.3203, -2.4707),
    "Leo": (11.1003, -2.1061),
    "Koupéla": (12.1777, -0.3569),
    "Titao": (13.7677, -2.0621),
    "Tougan": (13.0708, -3.0686),
    "Gorom-Gorom": (14.4500, -0.2333),
    "Diapaga": (12.0744, 1.7888),
    "Sebba": (13.4375, 0.5308),
    "Bogandé": (12.9683, -0.1433),
    "Zorgho": (12.2492, -0.6111),
    "Kombissiri": (12.0667, -1.3333),
    "Pô": (11.1833, -1.1500),
    "Dano": (11.1465, -3.0578),
    "Solenzo": (12.1833, -4.0833),
    "Orodara": (10.9667, -4.9333),
    "Sébba": (13.4375, 0.5308),
    "Boromo": (11.7487, -2.9305),
    "Fô": (10.2877, -4.9074),
    "Yaoundé": (3.8480, 11.5021),
    "Douala": (4.0511, 9.7679),
    "Garoua": (9.3351, 13.3874),
    "Bamenda": (5.9631, 10.1591),
    "Bafoussam": (5.4775, 10.4172),
    "Maroua": (10.5956, 14.3247),
    "Ngaoundéré": (7.3276, 13.5846),
    "Kumba": (4.6353, 9.4465),
    "Nkongsamba": (4.9601, 9.9404),
    "Bertoua": (4.5773, 13.6846),
    "Ebolowa": (2.9033, 11.1535),
    "Limbé": (4.0222, 9.2061),
    "Kribi": (2.9397, 9.9101),
    "Foumban": (5.7266, 10.8987),
    "Buea": (4.1511, 9.2411),
    "Dschang": (5.4541, 10.0538),
    "Edéa": (3.7989, 10.1333),
    "Mbouda": (5.6281, 10.2546),
    "Yagoua": (10.3408, 15.2347),
    "Meiganga": (6.5160, 14.2899),
    "Mbalmayo": (3.5189, 11.5011),
    "Tiko": (4.0742, 9.3654),
    "Sangmélima": (2.9333, 11.9833),
    "Guider": (9.9333, 13.9500),
    "Bafia": (4.7500, 11.2333),
    "Kaélé": (10.1041, 14.4525),
    "Banyo": (6.7500, 11.8167),
    "Batouri": (4.4333, 14.3667),
    "Mokolo": (10.7405, 13.8011),
    "Tibati": (6.4667, 12.6333),
    "Wum": (6.3908, 10.0685),
    "Ndop": (5.9615, 10.3925),
    "Eséka": (3.6500, 10.7667),
    "Akonolinga": (3.7667, 12.2500),
    "Obala": (4.1667, 11.5333),
    "Ambam": (2.3833, 11.2833),
    "Manjo": (4.8384, 9.8214),
    "Muyuka": (4.2854, 9.4104),
    "Mundemba": (4.9514, 8.8709),
    "Kousséri": (12.0783, 15.0300),
    "Bélabo": (4.9333, 13.3000),
    "Fontem": (5.4701, 9.8819),
    "Akonolinga": (3.7667, 12.2500),
    "Bamendjou": (5.4195, 10.3303),
    "Bangangté": (5.1418, 10.5156),
    "Foumbot": (5.5089, 10.6311),
    "Mamfé": (5.7512, 9.3144),
    "Libreville": (0.4162, 9.4673),
    "Port-Gentil": (-0.7193, 8.7815),
    "Franceville": (-1.6333, 13.5836),
    "Oyem": (1.6043, 11.5786),
    "Moanda": (-1.5658, 13.1987),
    "Mouila": (-1.8685, 11.0559),
    "Lambaréné": (-0.7001, 10.2405),
    "Tchibanga": (-2.8566, 11.0221),
    "Makokou": (0.5738, 12.8644),
    "Bitam": (2.0766, 11.5008),
    "Gamba": (-2.6497, 10.0009),
    "Lastoursville": (-0.8196, 12.7077),
    "Ntoum": (0.3926, 9.7600),
    "Koulamoutou": (-1.1320, 12.4753),
    "Booué": (-0.0922, 11.9387),
    "Mitzic": (0.7827, 11.5490),
    "Ndendé": (-2.3870, 11.3549),
    "Mayumba": (-3.4445, 10.6554),
    "Okondja": (-0.6543, 13.7838),
    "Fougamou": (-1.2160, 10.5833),
    "Mbigou": (-1.9277, 11.9058),
    "Omboué": (-1.5742, 9.2616),
    "Lekoni": (-1.5833, 14.2333),
    "Mékambo": (1.0221, 13.9721),
    "Minvoul": (2.1220, 12.0819),
    "Ndjolé": (-0.1776, 10.7661),
    "Lékoni": (-1.5906, 14.2584),
    "Lambaréné": (-0.7017, 10.2343),
    "Medouneu": (0.9624, 10.7562),
    "Conakry": (9.6412, -13.5784),
    "Nzérékoré": (7.7565, -8.8174),
    "Kankan": (10.3854, -9.3057),
    "Kindia": (10.0569, -12.8656),
    "Labé": (11.3182, -12.2833),
    "Kissidougou": (9.1900, -10.1208),
    "Guéckédou": (8.5677, -10.1326),
    "Mamou": (10.3732, -12.091),
    "Siguiri": (11.4228, -9.1684),
    "Dabola": (10.7430, -11.1083),
    "Faranah": (10.0404, -10.7432),
    "Macenta": (8.5435, -9.4715),
    "Boké": (10.9380, -14.2973),
    "Kouroussa": (10.6510, -9.8836),
    "Pita": (11.0704, -12.4010),
    "Fria": (10.3623, -13.5822),
    "Dalaba": (10.6770, -12.2532),
    "Tougué": (11.4407, -11.6641),
    "Dinguiraye": (11.2996, -10.7267),
    "Lélouma": (11.4212, -12.6834),
    "Telimélé": (10.9002, -13.0425),
    "Koundara": (12.4839, -13.2965),
    "Beyla": (8.6929, -8.6457),
    "Fôret": (9.6795, -13.6853),
    "Mali": (12.0836, -12.3014),
    "Youkounkoun": (12.5313, -13.1227),
    "Gaoual": (11.7543, -13.2077),
    "Kérouané": (9.2728, -9.0127),
    "Coyah": (9.7072, -13.3847),
    "Dubréka": (9.7796, -13.5112),
    "Mandiana": (10.6239, -8.7094),
    "Nairobi": (-1.286389, 36.817223),
    "Mombasa": (-4.043477, 39.668206),
    "Kisumu": (-0.091702, 34.768024),
    "Nakuru": (-0.303099, 36.080026),
    "Eldoret": (0.514277, 35.269779),
    "Thika": (-1.033270, 37.069327),
    "Kitale": (1.015861, 35.006210),
    "Malindi": (-3.218933, 40.116943),
    "Garissa": (-0.452735, 39.646012),
    "Kakamega": (0.282730, 34.751863),
    "Nanyuki": (0.009067, 37.073220),
    "Naivasha": (-0.716667, 36.433334),
    "Machakos": (-1.517683, 37.263414),
    "Nyeri": (-0.420133, 36.947593),
    "Meru": (0.047035, 37.649803),
    "Kericho": (-0.367662, 35.283290),
    "Isiolo": (0.354620, 37.582150),
    "Lamu": (-2.271944, 40.902778),
    "Moyale": (3.517571, 39.052720),
    "Marsabit": (2.339500, 37.989123),
    "Embu": (-0.539611, 37.457913),
    "Lodwar": (3.119841, 35.597296),
    "Homa Bay": (-0.527322, 34.457152),
    "Bungoma": (0.563793, 34.560963),
    "Narok": (-1.080217, 35.871936),
    "Kilifi": (-3.630401, 39.854381),
    "Voi": (-3.376585, 38.556046),
    "Migori": (-1.063639, 34.473077),
    "Makueni": (-1.804237, 37.631187),
    "Busia": (0.459310, 34.115390),
    "Wajir": (1.747044, 40.057324),
    "Mandera": (3.938427, 41.860502),
    "Keroka": (-0.768896, 34.944928),
    "Kapenguria": (1.238832, 35.111332),
    "Siaya": (0.061662, 34.291615),
    "Kimilili": (0.719618, 34.720871),
    "Taveta": (-3.405098, 37.682547),
    "Ruiru": (-1.165719, 36.964663),
    "Molo": (-0.248432, 35.737304),
    "Gilgil": (-0.492989, 36.331735),
    "Litein": (-0.580504, 35.162073),
    "Maralal": (1.096819, 36.696515),
    "Kajiado": (-1.853560, 36.776947),
    "Monrovia": (6.3004, -10.7969),
    "Gbarnga": (7.0050, -9.4717),
    "Kakata": (6.5312, -10.3537),
    "Harper": (4.3750, -7.7176),
    "Voinjama": (8.4219, -9.7477),
    "Buchanan": (5.8769, -10.0493),
    "Zwedru": (6.0675, -8.1350),
    "Greenville": (5.0111, -9.0388),
    "Robertsport": (6.7533, -11.3662),
    "Sanniquellie": (7.3622, -8.7147),
    "Tubmanburg": (6.8703, -10.8189),
    "Barclayville": (4.6735, -8.2335),
    "Foya": (8.3787, -10.2170),
    "River Cess": (5.4628, -9.5768),
    "Pleebo": (4.5750, -7.9658),
    "Bopolu": (6.9879, -10.4883),
    "Cestos City": (5.4563, -9.5817),
    "Karnplay": (7.2439, -8.5295),
    "New Yekepa": (7.5792, -8.5389),
    "Careysburg": (6.4292, -10.5147),
    "Tchien": (6.0667, -8.1333),
    "Salala": (6.9344, -10.2861),
    "Buchanan": (5.8808, -10.0430),
    "Tapeta": (6.4978, -8.8684),
    "Sagleipie": (7.3675, -8.6127),
    "Bamako": (12.6392, -8.0029),
    "Sikasso": (11.3170, -5.6665),
    "Kayes": (14.4444, -11.4393),
    "Mopti": (14.4843, -4.1829),
    "Ségou": (13.4317, -6.2157),
    "Koutiala": (12.3917, -5.4647),
    "Gao": (16.2667, -0.0500),
    "Timbuktu": (16.7735, -3.0083),
    "Kati": (12.7441, -8.0726),
    "Nioro du Sahel": (15.2233, -9.5700),
    "Markala": (13.6833, -6.0667),
    "Kolokani": (13.5817, -8.0337),
    "San": (13.3037, -4.8957),
    "Bougouni": (11.4177, -7.4837),
    "Douentza": (15.0031, -2.9519),
    "Koulikoro": (12.8628, -7.5606),
    "Banamba": (13.5472, -7.4481),
    "Dioila": (12.1958, -6.8063),
    "Bafoulabé": (13.8064, -10.8325),
    "Yorosso": (12.3586, -4.7797),
    "Goundam": (16.4145, -3.6696),
    "Diré": (16.2700, -3.3959),
    "Nara": (15.1687, -7.2833),
    "Ansongo": (15.6603, 0.5022),
    "Diéma": (14.5082, -9.1954),
    "Kangaba": (11.9338, -8.4162),
    "Djenné": (13.9060, -4.5556),
    "Ténenkou": (14.4584, -4.9152),
    "Kidal": (18.4411, 1.4078),
    "Menaka": (15.9161, 2.4022),
    "Lagos": (6.5244, 3.3792),
    "Abuja": (9.0765, 7.3986),
    "Kano": (12.0022, 8.5919),
    "Ibadan": (7.3775, 3.9470),
    "Port Harcourt": (4.8156, 7.0498),
    "Benin City": (6.3392, 5.6174),
    "Maiduguri": (11.8333, 13.1500),
    "Zaria": (11.0855, 7.7199),
    "Jos": (9.9285, 8.8921),
    "Ogbomosho": (8.1339, 4.2436),
    "Warri": (5.5544, 5.7932),
    "Kaduna": (10.5105, 7.4165),
    "Abeokuta": (7.1501, 3.3460),
    "Sokoto": (13.0059, 5.2476),
    "Onitsha": (6.1427, 6.7857),
    "Enugu": (6.5246, 7.5189),
    "Ilorin": (8.5000, 4.5500),
    "Ife": (7.4850, 4.5544),
    "Osogbo": (7.7710, 4.5567),
    "Akure": (7.2508, 5.2103),
    "Bauchi": (10.3103, 9.8439),
    "Owerri": (5.4850, 7.0354),
    "Calabar": (4.9589, 8.3269),
    "Gombe": (10.2897, 11.1673),
    "Uyo": (5.0370, 7.9128),
    "Katsina": (12.9908, 7.6018),
    "Ado-Ekiti": (7.6233, 5.2200),
    "Minna": (9.6152, 6.5478),
    "Makurdi": (7.7339, 8.5217),
    "Oyo": (7.8500, 3.9333),
    "Ilesa": (7.6295, 4.7400),
    "Lokoja": (7.8014, 6.7430),
    "Ikot Ekpene": (5.1819, 7.7144),
    "Yola": (9.2035, 12.4957),
    "Umuahia": (5.5320, 7.4860),
    "Gusau": (12.1702, 6.6640),
    "Birnin Kebbi": (12.4546, 4.1976),
    "Jalingo": (8.8937, 11.3596),
    "Damaturu": (11.7460, 11.9608),
    "Nnewi": (6.0167, 6.9167),
    "Bida": (9.0805, 6.0140),
    "Ede": (7.7407, 4.4348),
    "Ijebu-Ode": (6.8188, 3.9174),
    "Ugep": (5.8000, 8.0833),
    "Shagamu": (6.8498, 3.6461),
    "Oturkpo": (7.1929, 8.1395),
    "Kampala": (0.3476, 32.5825),
    "Entebbe": (0.0512, 32.4637),
    "Jinja": (0.4390, 33.2032),
    "Gulu": (2.7724, 32.2881),
    "Mbarara": (-0.6079, 30.6545),
    "Fort Portal": (0.6612, 30.2758),
    "Mbale": (1.0821, 34.1750),
    "Lira": (2.2493, 32.8998),
    "Soroti": (1.7020, 33.6117),
    "Hoima": (1.4356, 31.3436),
    "Arua": (3.0201, 30.9110),
    "Masaka": (-0.3334, 31.7341),
    "Kabale": (-1.2483, 29.9899),
    "Tororo": (0.6846, 34.1810),
    "Mukono": (0.3533, 32.7554),
    "Kasese": (0.1833, 30.0833),
    "Iganga": (0.6092, 33.4687),
    "Kitgum": (3.2783, 32.8867),
    "Busia": (0.4646, 34.0914),
    "Bushenyi": (-0.5395, 30.1989),
    "Luwero": (0.8492, 32.4735),
    "Ntungamo": (-0.8791, 30.2642),
    "Mityana": (0.4173, 32.0223),
    "Kamuli": (0.9470, 33.1190),
    "Pallisa": (1.1458, 33.7094),
    "Nebbi": (2.4783, 31.1028),
    "Bombo": (0.5833, 32.5333),
    "Koboko": (3.4137, 30.9590),
    "Kapchorwa": (1.3848, 34.4436),
    "Nakasongola": (1.3081, 32.4564),
    "Moroto": (2.5342, 34.6666),
    "Masindi": (1.6744, 31.7150),
    "Rukungiri": (-0.8410, 29.9415),
    "Kamwenge": (0.1828, 30.4522),
    "Kanungu": (-0.9508, 29.7814),
    "Apac": (1.9842, 32.5389),
    "Kaliro": (1.0004, 33.5157),
    "Mayuge": (0.4597, 33.4809),
    "Busembatia": (0.7718, 33.6117),
    "Kigali": (-1.9706, 30.1044),
    "Butare": (-2.5981, 29.7401),
    "Gisenyi": (-1.7010, 29.2565),
    "Musanze": (-1.4998, 29.6349),
    "Byumba": (-1.5786, 30.0675),
    "Gitarama": (-2.0744, 29.7569),
    "Rwamagana": (-1.9487, 30.4347),
    "Kibuye": (-2.0603, 29.3485),
    "Cyangugu": (-2.4778, 28.9075),
    "Kibungo": (-2.1597, 30.5430),
    "Nyagatare": (-1.5026, 30.4668),
    "Ruhengeri": (-1.4998, 29.6349),
    "Muhanga": (-2.0723, 29.7565),
    "Gikongoro": (-2.6215, 29.5802),
    "Nyanza": (-2.3494, 29.7500),
    "Nyamasheke": (-2.3210, 29.0260),
    "Karongi": (-2.0636, 29.3461),
    "Ngoma": (-2.1539, 30.5051),
    "Rubavu": (-1.6767, 29.3722),
    "Kamembe": (-2.4815, 28.9090),
    "Dakar": (14.6928, -17.4467),
    "Thiès": (14.7892, -16.9260),
    "Saint-Louis": (16.0179, -16.4896),
    "Ziguinchor": (12.5644, -16.2719),
    "Kaolack": (14.1825, -16.2533),
    "Touba": (14.8618, -15.8749),
    "Mbour": (14.4296, -16.9666),
    "Tambacounda": (13.7700, -13.6673),
    "Kolda": (12.8922, -14.9415),
    "Kédougou": (12.5556, -12.1863),
    "Louga": (15.6101, -16.2240),
    "Diourbel": (14.6568, -16.2317),
    "Podor": (16.6560, -14.9610),
    "Matam": (15.6559, -13.2554),
    "Sédhiou": (12.7075, -15.5569),
    "Fatick": (14.3435, -16.4159),
    "Rufisque": (14.7218, -17.2744),
    "Bignona": (12.8103, -16.2266),
    "Bakel": (14.9006, -12.4650),
    "Kaffrine": (14.1056, -15.5508),
    "Richard-Toll": (16.4635, -15.6946),
    "Joal-Fadiouth": (14.1667, -16.8333),
    "Tivaouane": (15.0040, -16.8455),
    "Pikine": (14.7645, -17.3907),
    "Guédiawaye": (14.7732, -17.3733),
    "Médina": (14.7798, -17.4065),
    "Lomé": (6.1319, 1.2227),
    "Sokodé": (8.9833, 1.1333),
    "Kara": (9.5511, 1.1861),
    "Atakpamé": (7.5333, 1.1333),
    "Kpalimé": (6.9000, 0.6333),
    "Tsevié": (6.4261, 1.2129),
    "Aného": (6.2333, 1.6000),
    "Dapaong": (10.8639, 0.2050),
    "Bassar": (9.2500, -0.7833),
    "Niamtougou": (9.7689, 1.1053),
    "Mango": (10.3592, 0.4708),
    "Sotouboua": (8.5633, 0.9836),
    "Tabligbo": (6.5833, 1.5000),
    "Notse": (6.9500, 1.1667),
    "Bafilo": (9.3500, 1.2667),
    "Kandé": (9.9572, 1.0447),
    "Amlamé": (7.4667, 0.9000),
    "Badou": (7.5833, 0.6000),
    "Pagouda": (9.7558, 1.3275),
    "Vogan": (6.3333, 1.5333),
    "Freetown": (8.4657, -13.2317),
    "Bo": (7.9655, -11.7353),
    "Kenema": (7.8761, -11.1900),
    "Makeni": (8.8860, -12.0442),
    "Koidu": (8.6448, -10.9712),
    "Port Loko": (8.7661, -12.7864),
    "Kabala": (9.5881, -11.5526),
    "Magburaka": (8.7167, -11.9481),
    "Lunsar": (8.6847, -12.5344),
    "Waterloo": (8.3389, -13.0708),
    "Bonthe": (7.5264, -12.5050),
    "Segbwema": (7.9942, -10.9506),
    "Kambia": (9.1266, -12.9294),
    "Moyamba": (8.1595, -12.4330),
    "Pujehun": (7.3577, -11.7124),
    "Tongo": (8.0136, -11.6729),
    "Kailahun": (8.2800, -10.5769),
    "Masingbi": (8.8833, -11.3833),
    "Pepel": (8.5854, -13.0484),
    "Yengema": (8.6772, -11.0379),
    "Addis Abeba": (9.0301, 38.7427),
    "Dire Dawa": (9.5931, 41.8661),
    "Mekelle": (13.4967, 39.4753),
    "Gondar": (12.6000, 37.4667),
    "Hawassa": (7.0500, 38.4667),
    "Bahir Dar": (11.6000, 37.3833),
    "Adama (Nazret)": (8.5500, 39.2667),
    "Harar": (9.3094, 42.1305),
    "Jijiga": (9.3500, 42.8000),
    "Jimma": (7.6667, 36.8333),
    "Debre Birhan": (9.6797, 39.5327),
    "Shashamane": (7.2000, 38.6000),
    "Arba Minch": (6.0333, 37.5500),
    "Dessie": (11.1333, 39.6333),
    "Debre Markos": (10.3333, 37.7333),
    "Asella": (7.9500, 39.1333),
    "Nekemte": (9.0917, 36.5300),
    "Gambela": (8.2500, 34.5833),
    "Dilla": (6.4167, 38.3167),
    "Weldiya": (11.8333, 39.6000),
    "Sodo": (6.9000, 37.7500),
    "Hosaena": (7.5500, 37.8500),
    "Goba": (7.0167, 39.9833),
    "Aksoum": (14.1211, 38.7219),
    "Mojo": (8.5868, 39.1165),
    "Metu": (8.3000, 35.5833),
    "Adigrat": (14.2760, 39.4600),
    "Ziway": (7.9333, 38.7167),
    "Semen Shewa Zone": (10.0000, 39.5000),
    "Brazzaville": (-4.2634, 15.2429),
    "Pointe-Noire": (-4.7848, 11.8651),
    "Dolisie": (-4.1979, 12.6666),
    "Nkayi": (-4.1806, 13.2899),
    "Owando": (-0.4802, 15.8992),
    "Oyo": (-1.2167, 15.9333),
    "Impfondo": (1.6189, 18.0597),
    "Madingou": (-4.1536, 13.5450),
    "Sibiti": (-3.6812, 13.3496),
    "Mossendjo": (-2.9500, 12.7333),
    "Kinkala": (-4.3569, 14.7647),
    "Gamboma": (-1.8764, 15.8645),
    "Ewo": (-0.8724, 14.8209),
    "Makoua": (-0.0067, 15.6403),
    "Kayes": (-4.1879, 13.2847),
    "Mossaka": (-1.9264, 16.7706),
    "Loubomo": (-4.1984, 12.6772),
    "Lékana": (-2.1454, 14.7913),
    "Djambala": (-2.5392, 14.7530),
    "Ouesso": (1.6136, 16.0517),
    "Ngamaba-Mfilou": (-4.3340, 15.2570),
    "Ewo": (0.8700, 14.8100),
    "Kelle": (-0.1310, 14.6463),
    "Sembé": (1.6500, 14.5810),
    "Lékoumou": (-2.9448, 12.7312),
    "Kinshasa": (-4.4419, 15.2663),
    "Lubumbashi": (-11.6873, 27.4794),
    "Mbuji-Mayi": (-6.1360, 23.5898),
    "Kisangani": (0.5153, 25.1904),
    "Kananga": (-5.8973, 22.4185),
    "Bukavu": (-2.5090, 28.8407),
    "Goma": (-1.6585, 29.2204),
    "Matadi": (-5.8383, 13.4637),
    "Likasi": (-10.9803, 26.7333),
    "Kolwezi": (-10.7167, 25.4721),
    "Tshikapa": (-6.4166, 20.7990),
    "Mwene-Ditu": (-7.0101, 23.4436),
    "Boma": (-5.8486, 13.0486),
    "Uvira": (-3.3959, 29.1373),
    "Beni": (0.4905, 29.4739),
    "Kalemie": (-5.9475, 29.1947),
    "Isiro": (2.7746, 27.6160),
    "Mbandaka": (0.0466, 18.2603),
    "Butembo": (0.1397, 29.2913),
    "Kindu": (-2.9474, 25.9229),
    "Gemena": (3.2561, 19.7712),
    "Bunia": (1.5606, 30.2527),
    "Kikwit": (-5.0401, 18.8162),
    "Kabinda": (-6.1357, 24.4828),
    "Basankusu": (1.2240, 19.7970),
    "Lisala": (2.1463, 21.5167),
    "Inongo": (-1.9260, 18.2853),
    "Lodja": (-3.4833, 23.4333),
    "N'Djamena": (12.1348, 15.0557),
    "Moundou": (8.5662, 16.0773),
    "Sarh": (9.1429, 18.3923),
    "Abéché": (13.8292, 20.8324),
    "Kélo": (9.3085, 15.8066),
    "Pala": (9.3642, 14.9046),
    "Am Timan": (11.0297, 20.2822),
    "Bongor": (10.2806, 15.3729),
    "Mongo": (12.1840, 18.6930),
    "Doba": (8.6500, 16.8500),
    "Ati": (13.2154, 18.3365),
    "Massaguet": (12.4756, 15.4427),
    "Faya-Largeau": (17.9254, 19.1043),
    "Biltine": (14.5324, 20.9271),
    "Oum Hadjer": (13.2955, 19.6900),
    "Goz Beïda": (12.2235, 21.4106),
    "Bokoro": (12.3784, 17.0573),
    "Bitkine": (11.9804, 18.2138),
    "Massakory": (12.9961, 15.7290),
    "Moussoro": (13.6410, 16.4897),
    "Léré": (9.9667, 14.2667),
    "Laï": (9.3951, 16.3003),
    "Bebedjia": (8.6833, 16.5667),
    "Koumra": (8.9127, 17.5533),
    "Faya": (17.9167, 19.1000),
    "Ndélé": (8.4106, 20.6512),
    "Goundi": (9.3675, 17.3669),
    "Béré": (9.3333, 16.1500),
    "Niamey": (13.5116, 2.1254),
    "Zinder": (13.8072, 8.9881),
    "Maradi": (13.5000, 7.1017),
    "Tahoua": (14.8888, 5.2692),
    "Agadez": (16.9733, 7.9911),
    "Dosso": (13.0499, 3.1939),
    "Diffa": (13.3153, 12.6113),
    "Tillabéri": (14.2131, 1.4531),
    "Arlit": (18.7369, 7.3853),
    "Birni-N'Konni": (13.7942, 5.2509),
    "Tessaoua": (13.7577, 7.9874),
    "Gaya": (11.8843, 3.4522),
    "Madaoua": (14.0731, 5.9603),
    "Magaria": (12.9982, 8.9097),
    "Illela": (14.4579, 5.2393),
    "Téra": (14.0073, 0.7533),
    "Tchintabaraden": (15.8932, 5.8007),
    "Nguigmi": (14.2522, 13.1092),
    "Say": (13.1089, 2.3585),
    "Mainé-Soroa": (13.2170, 12.0266),
    "Dogondoutchi": (13.6436, 4.0284),
    "Matameye": (13.4232, 8.4747),
    "Tanout": (14.9703, 8.8912),
    "Filingué": (14.3525, 3.3174),
    "Ayorou": (14.7319, 0.9196)
}
# Paramètres pour la grille (2 km x 2 km par case, 10x10 zones)
lat_step = 0.018  # Environ 2 km en latitude
lon_step = 0.018  # Environ 2 km en longitude
num_lat = 10      # 10 zones en latitude
num_lon = 10      # 10 zones en longitude

# DataFrame pour stocker toutes les pharmacies
all_pharmacies = pd.DataFrame()
# Boucle sur chaque ville
for city, coordinates in cities_coordinates.items():
    lat_center, lon_center = coordinates
    print(f"Traitement de la ville : {city}")

    # Générer la grille de points
    zones = generate_zones(lat_center, lon_center, lat_step, lon_step, num_lat, num_lon)

    # Liste pour stocker les pharmacies de cette ville
    city_pharmacies = []

    # Récupérer les pharmacies pour chaque zone
    for zone in zones:
        pharmacies = get_pharmacies_osm(latitude=zone[0], longitude=zone[1], radius=1000)
        city_pharmacies.extend(pharmacies)

    # Ajouter la colonne pour indiquer la ville
    df_city_pharmacies = pd.DataFrame(city_pharmacies)
    df_city_pharmacies['city'] = city

    # Ajouter au DataFrame général
    all_pharmacies = pd.concat([all_pharmacies, df_city_pharmacies], ignore_index=True)

    # Générer la carte pour la ville
    osm_map = folium.Map(location=[lat_center, lon_center], zoom_start=12)

    # Ajouter des marqueurs pour chaque pharmacie
    for _, row in df_city_pharmacies.iterrows():
        folium.Marker(location=[row['latitude'], row['longitude']],
                      popup=f"Pharmacy: {row['name']}").add_to(osm_map)

    # Sauvegarder et capturer la carte de la ville
    map_filename = f"map_{city}.png"
    capture_map(osm_map, map_filename)

# Supprimer les doublons basés sur le nom, la latitude et la longitude
all_pharmacies_unique = all_pharmacies.drop_duplicates(subset=['name', 'latitude', 'longitude'])

# Afficher le nombre de pharmacies après suppression des doublons
print(f"Nombre total de pharmacies après suppression des doublons : {len(all_pharmacies_unique)}")

# Sauvegarder le DataFrame final dans un fichier CSV
csv_filename = "pharmacies_complet_sans_doublons_Afrique.csv"
all_pharmacies_unique.to_csv(csv_filename, index=False)

# Télécharger le fichier CSV
files.download(csv_filename)