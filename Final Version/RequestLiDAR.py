import geopandas as gpd
import requests
from tqdm import tqdm
import os
import math
import numpy as np

from utils import create_output_folder

def __getTiles(bounds, buffer_size=0):
    minx, miny, maxx, maxy = bounds
    minx -= buffer_size
    miny -= buffer_size
    maxx += buffer_size
    maxy += buffer_size

    minx_tile = math.floor(minx / 1000)
    maxx_tile = math.floor(maxx / 1000)
    miny_tile = math.floor(miny / 1000)%4000
    maxy_tile = math.floor(maxy / 1000)%4000

    tiles = [
        f"{minx_tile}{miny_tile}",
        f"{maxx_tile}{miny_tile}",
        f"{minx_tile}{maxy_tile}",
        f"{maxx_tile}{maxy_tile}",
    ]
    return np.unique(tiles)

def __obtainNecessaryLiDARs(parcelsFolder, buffer):
    sheetList = []
    for parcel in os.listdir(parcelsFolder):
        gdfPath = parcelsFolder + "/" + parcel + "/" + parcel + ".gpkg"
        parcelGDF = gpd.read_file(gdfPath)
        bounds = parcelGDF.total_bounds # [minx, miny, maxx, maxy]
        # Unbuffered
        unbuffered_tiles = __getTiles(bounds)
        unbuffered_path = os.path.join(parcelsFolder, parcel, "necessaryLiDAR.txt")
        with open(unbuffered_path, 'w') as f:
            for tile in unbuffered_tiles:
                f.write(tile + ".laz\n")

        # Buffered
        buffered_tiles = __getTiles(bounds, buffer)
        buffered_path = os.path.join(parcelsFolder, parcel, f"necessaryLiDAR_{buffer}m.txt")
        with open(buffered_path, 'w') as f:
            for tile in buffered_tiles:
                f.write(tile + ".laz\n")

        sheetList.extend(buffered_tiles)

    return np.unique(sheetList)


def __download_LIDAR_CAT(squares, outputFolder):
    base_url = "https://datacloud.icgc.cat/datacloud/lidar-territorial/laz_unzip/"    
    for square in tqdm(squares, desc="Downloading LiDAR data"):
        mainZone = int(str(square)[0:2] + str(square)[3:5])
        url = base_url + f"full10km{mainZone}/" + f"lidar-territorial-v3r0-full1km{square}-2021-2023.laz"
        filename = outputFolder + f"{square}.laz"

        if os.path.exists(filename):
            continue

        response = requests.get(url, stream=True)
        with open(filename, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192): 
                file.write(chunk)

def download_LiDAR(downloadFolder, parcelsFolder, buffer=50):
    create_output_folder(downloadFolder)
    sheetList = __obtainNecessaryLiDARs(parcelsFolder, buffer)
    __download_LIDAR_CAT(sheetList, downloadFolder)
    pass