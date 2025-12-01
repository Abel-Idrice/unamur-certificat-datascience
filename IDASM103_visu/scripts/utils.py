import numpy as np
import geopandas as gpd
import pandas as pd
from shapely import wkt

def populate_unknown_borough(df):
    """
        This function populates the borough name based on the latitude and longitude of the entry
        requires: df with lat and long fields (numeric)
    """
    BOROUGHTS_BOUNDARIES = gpd.read_file("../data/raw/Borough_Boundaries_20251110.geojson")

    gdf_unknown = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.long, df.lat),
        crs="EPSG:4326"
    ) 

    joined = gpd.sjoin(gdf_unknown, BOROUGHTS_BOUNDARIES, how="left", predicate="within")

    joined = joined.rename(columns={'boroname': 'BOROUGH NAME'})

    borough_info = joined[['BOROUGH NAME']].copy()
    borough_info.index = joined.index

    return borough_info


def populate_neighbourhood(df, nta_csv_path="../data/raw/2020_Neighborhood_Tabulation_Areas_(NTAs)_20251117.csv"):
    """
    Ajoute le quartier (NTA) correspondant à chaque point (longitude, latitude)
    à partir du fichier CSV des NTAs contenant une colonne WKT 'the_geom'.

    Paramètres
    ----------
    df : pandas.DataFrame
        Doit contenir 'longitude' et 'latitude'.
    nta_csv_path : str
        Fichier CSV contenant les polygones NTA au format WKT.

    Return
    ------
    pandas.DataFrame
        Colonnes ajoutées : NTA2020, NTAName, NTAAbbrev
    """

    # Charger le CSV NTA
    nta_df = pd.read_csv(nta_csv_path)

    # Convertir la géométrie WKT → objet shapely
    nta_df["geometry"] = nta_df["the_geom"].apply(wkt.loads)

    # Construire GeoDataFrame des NTA
    gdf_nta = gpd.GeoDataFrame(nta_df, geometry="geometry", crs="EPSG:4326")

    # Construire GeoDataFrame des points (df initial)
    gdf_points = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs="EPSG:4326"
    )

    # Jointure spatiale
    joined = gpd.sjoin(gdf_points, gdf_nta, how="left", predicate="within")

    # Colonnes à extraire
    neighbourhood_info = joined[["NTA2020", "NTAName", "NTAAbbrev"]].copy()
    neighbourhood_info.index = df.index  # conserver index original

    return neighbourhood_info



def add_fake_reviews(df, seed=42):
    np.random.seed(seed)

    n_reviews = np.random.lognormal(mean=1.5, sigma=1.0, size=len(df)).astype(int)

    score_choices = [1, 2, 3, 4, 5]
    probabilities = [0.05, 0.10, 0.20, 0.35, 0.30]

    base_scores = np.random.choice(score_choices, size=len(df), p=probabilities)

    # 3. Ajustement : plus il y a de reviews, plus le score se stabilise vers 4–5
    adjusted_scores = []
    for score, n in zip(base_scores, n_reviews):
        if n < 5:
            # très variable
            s = np.random.randint(1, 6)
        elif n < 50:
            # légèrement biaisé vers le base_score
            s = int(np.clip(np.random.normal(loc=score, scale=0.7), 1, 5))
        else:
            # gros nombre de reviews → score élevé
            s = int(np.clip(np.random.normal(loc=max(score, 4), scale=0.4), 1, 5))
        adjusted_scores.append(s)

    df["Number_of_reviews"] = n_reviews
    df["Review_score"] = adjusted_scores
    return df
