import os
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
import math
import laspy #https://stackoverflow.com/questions/71641718/what-is-the-laspy-error-when-reading-laz-files

def getLidarParcels(directory, lazPath, buffer = 200):
    filenames = []
    for folder in os.listdir(directory):
        parcelFile = directory + folder + "/" + folder +  ".gpkg"
        parcel_gdf = gpd.read_file(parcelFile)
        bounds = parcel_gdf.geometry.bounds
        minX, minY, maxX, maxY = bounds.minx[0] - buffer, bounds.miny[0] - buffer, bounds.maxx[0] + buffer, bounds.maxy[0] + buffer
        
        minXstr, minYstr, maxXstr, maxYstr = str(math.floor(minX/1000)), str(math.floor(minY/1000))[-3:], str(math.floor(maxX/1000)), str(math.floor(maxY/1000))[-3:]
        # filenames = [minXstr + minYstr, maxXstr + minYstr, minXstr + maxYstr, maxXstr + maxYstr]
        filenames.append(minXstr + minYstr)
        filenames.append(maxXstr + minYstr)
        filenames.append(minXstr + maxYstr)
        filenames.append(maxXstr + maxYstr)
    filenames = set(filenames)
    # lasfiles = []
    # for file in filenames:
    #     lasfiles.append(laspy.read(lazPath + file + ".laz"))
    print(filenames)

if __name__ == "__main__":
    basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
    neighborhood = "70_el Besòs i el Maresme"
    directory = basePath + "Results/" + neighborhood + "/Parcels/"
    lazPath = "RAW_Data/LiDAR/"
    getLidarParcels(directory, lazPath)