import scrape
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import geopandas as gpd
from tqdm import tqdm
import pandas as pd
import re
from dotenv import load_dotenv
import os

load_dotenv()
locator = Nominatim(user_agent="spatialthoughts", timeout=10)
geocode = RateLimiter(locator.geocode, min_delay_seconds=1)

def find_location(row):
    if (row['location']):
        return geocode(row['full_address'])
    else:
        return row['location']

def scrape_data(n_pages=500, min_price=500000, max_price=1250000, min_plot_area=750, min_floor_area=110):
    scraper = scrape.FundaScraper(
        area="nl",
        want_to="buy",
        find_past=False,
        page_start=1,
        n_pages=n_pages,
        publication_date=1,
        min_price=min_price,
        max_price=max_price,
        min_plot_area=min_plot_area,
        min_floor_area=min_floor_area
    )

    df = scraper.run(raw_data=True)

    df['combined_address'] = df['address'] + ", " + \
        df['zip_code'] + " " + df['city'] + ' Netherlands'
    df['full_address'] = df['combined_address'].apply(
        lambda x: re.sub(r'\((.*?)\)', '', x))

    path = os.getenv('file_path_raw')
    df.to_csv(f'{path}.csv')

def geocode_data():
    input_path = os.getenv('file_path_raw')
    output_path = os.getenv('file_path_recent')
    historical_path = os.getenv('file_path_historical')
    df = pd.read_csv(f'{input_path}.csv')

    if (os.path.exists(f'{historical_path}.geojson')):
        gdf_historical = gpd.read_file(
            f'{historical_path}.geojson', driver='GeoJSON')

        gdf_historical = gdf_historical.loc[gdf_historical['location'] != ""]
        gdf_historical = gdf_historical[[
            'url', 'location', 'latitude', 'longitude']]
        gdf_historical.drop_duplicates(['url'])

        df_merged = df.merge(gdf_historical, how='left', on='url')
        df_geolocated = df_merged.loc[df_merged['location'].notna()]
        df_not_geolocated = df_merged.loc[df_merged['location'].isna()]

        tqdm.pandas()
        df_not_geolocated['location'] = df_not_geolocated['full_address'].progress_apply(
            geocode)

        df_not_geolocated['latitude'] = df_not_geolocated['location'].apply(
            lambda loc: loc.latitude if loc else None)
        df_not_geolocated['longitude'] = df_not_geolocated['location'].apply(
            lambda loc: loc.longitude if loc else None)

        df = pd.concat([df_geolocated, df_not_geolocated])

    else:
        tqdm.pandas()
        df['location'] = df['full_address'].progress_apply(geocode)
        df['latitude'] = df['location'].apply(
            lambda loc: loc.latitude if loc else None)
        df['longitude'] = df['location'].apply(
            lambda loc: loc.longitude if loc else None)

    geometry = gpd.points_from_xy(df.longitude, df.latitude)
    gdf = gpd.GeoDataFrame(df, crs='EPSG:4326', geometry=geometry)

    gdf = gdf.to_crs('EPSG:28992')

    if (os.path.exists(f'{output_path}.geojson')):
        print('do stuff here')
        if (os.path.exists(f'{historical_path}.geojson')):
            os.remove(f'{historical_path}.geojson')

        os.rename(f'{output_path}.geojson', f'{historical_path}.geojson')

    gdf.to_file(f'{output_path}.geojson', driver='GeoJSON')
