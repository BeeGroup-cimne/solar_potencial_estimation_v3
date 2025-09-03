import requests
import time
import configparser
import geopandas as gpd
import zipfile
import io
import os
from utils import create_output_folder

from shapely.ops import transform
from pyproj import Transformer


def getLatLon(cadasterPath):
    cadasterGDF = gpd.read_file(cadasterPath)
    projected_gdf = cadasterGDF.to_crs(cadasterGDF.estimate_utm_crs())
    centroids_proj = projected_gdf.geometry.centroid

    avg_centroid_proj = centroids_proj.union_all().centroid
    # avg_centroid_geo = gpd.GeoSeries([avg_centroid_proj], crs=projected_gdf.crs).to_crs(epsg=4326).geometry[0]
    transformer = Transformer.from_crs(projected_gdf.crs, "EPSG:4326", always_xy=True)

    # Apply directly on the point
    avg_centroid_geo = transform(transformer.transform, avg_centroid_proj)

    return avg_centroid_geo.y, avg_centroid_geo.x

def get_response_json_and_handle_errors(response: requests.Response) -> dict:
    """Takes the given response and handles any errors, along with providing
    the resulting json

    Parameters
    ----------
    response : requests.Response
        The response object

    Returns
    -------
    dict
        The resulting json
    """
    if response.status_code != 200:
        print(f"An error has occurred with the server or the request. The request response code/status: {response.status_code} {response.reason}")
        print(f"The response body: {response.text}")
        exit(1)

    try:
        response_json = response.json()
    except:
        print(f"The response couldn't be parsed as JSON, likely an issue with the server, here is the text: {response.text}")
        exit(1)

    if len(response_json['errors']) > 0:
        errors = '\n'.join(response_json['errors'])
        print(f"The request errored out, here are the errors: {errors}")
        exit(1)
    return response_json

def requestTMY(lat, lon):
    config = configparser.ConfigParser()
    config.read('Final Version/config.ini')
    API_KEY = config["NREL"]["API_KEY"]
    EMAIL = config["NREL"]["EMAIL"]

    BASE_URL = "https://developer.nrel.gov/api/nsrdb/v2/solar/nsrdb-msg-v1-0-0-tmy-download.json?"

    input_data = {
        'attributes': 'air_temperature,alpha,aod,asymmetry,clearsky_dhi,clearsky_dni,clearsky_ghi,cloud_type,dew_point,dhi,dni,fill_flag,ghi,relative_humidity,solar_zenith_angle,surface_albedo,surface_pressure,total_precipitable_water,wind_direction,wind_speed',
        'interval': '60',
        'email': EMAIL,
        'api_key': API_KEY
    }

    input_data['names'] = "tmy"
    input_data["wkt"] = f"POINT({round(lon, 2)} {round(lat, 2)})"

    headers = {
        'x-api-key': API_KEY
    }
    data = get_response_json_and_handle_errors(requests.post(BASE_URL, input_data, headers=headers))
    download_url = data['outputs']['downloadUrl']
    # Delay for 1 second to prevent rate limiting
    time.sleep(1)
    return download_url

def download_and_extract_csv(url, output_dir):
    while True:
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors
            break
        except:
            pass
    
    # Open the ZIP file from bytes
    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
        # Find the single CSV file
        csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
        if len(csv_files) != 1:
            raise ValueError(f"Expected 1 CSV file, found {len(csv_files)}")

        # Extract the CSV file
        csv_file = csv_files[0]
        csv_basename = os.path.basename(csv_file)
        with zip_ref.open(csv_file) as source, open(os.path.join(output_dir, csv_basename), 'wb') as target:
            target.write(source.read())
    
def downloadTMY(cadasterPath, outputFolder):
    create_output_folder(outputFolder)

    lat, lon = getLatLon(cadasterPath)
    url = requestTMY(lat, lon)
    download_and_extract_csv(url, outputFolder)

if __name__ == "__main__":
    pass