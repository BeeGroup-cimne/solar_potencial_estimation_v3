import os
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
import pandas as pd
import math
import json
import laspy #https://stackoverflow.com/questions/71641718/what-is-the-laspy-error-when-reading-laz-files

def getNecessaryLidarParcels(directory, buffer = 200):
    filenames = []
    cadasters = []
    corners = []
    for folder in os.listdir(directory):
        parcelFile = directory + folder + "/" + folder +  ".gpkg"
        parcel_gdf = gpd.read_file(parcelFile)
        bounds = parcel_gdf.geometry.bounds
        minX, minY, maxX, maxY = bounds.minx[0] - buffer, bounds.miny[0] - buffer, bounds.maxx[0] + buffer, bounds.maxy[0] + buffer
        
        minXstr, minYstr, maxXstr, maxYstr = str(math.floor(minX/1000)), str(math.floor(minY/1000))[-3:], str(math.floor(maxX/1000)), str(math.floor(maxY/1000))[-3:]
        files = [minXstr + minYstr, maxXstr + minYstr, minXstr + maxYstr, maxXstr + maxYstr]
        files.sort()
        files = set(files)
        files = list(files)
        filenames.append(files)
        cadasters.append(folder)
        corners.append([minX, minY, maxX, maxY])

    lidarsNeeded_df = pd.DataFrame({'REFCAT': cadasters, 'files':filenames, 'bounds':corners})
    lidarsNeeded_df['file_count'] = lidarsNeeded_df.files.apply(len)
    lidarsNeeded_df.files = lidarsNeeded_df.files.apply(json.dumps)
    lidarsNeeded_df = lidarsNeeded_df.sort_values(['file_count'])
    return lidarsNeeded_df



if __name__ == "__main__":
    basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
    neighborhood = "70_el Besòs i el Maresme"
    directory = basePath + "Results/" + neighborhood + "/Parcels/"

    lidarsNeeded_df = getNecessaryLidarParcels(directory, buffer = 100)
    listPath = basePath + "Results/" + neighborhood + "/necessaryLiDAR_Buffer100.txt"
    lidarsNeeded_df.to_csv(listPath, index = False)

    lidarsNeeded_df = getNecessaryLidarParcels(directory, buffer = 0)
    listPath = basePath + "Results/" + neighborhood + "/necessaryLiDAR.txt"
    lidarsNeeded_df.to_csv(listPath, index = False)