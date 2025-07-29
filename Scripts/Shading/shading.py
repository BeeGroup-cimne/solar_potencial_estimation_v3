import os
import numpy as np
import pandas as pd
import laspy
import json
import geopandas as gpd
import pygmt
from shapely.geometry import Point, MultiPolygon
import math
import shutil
from tqdm import tqdm
from collections import defaultdict
import contextlib

import warnings
warnings.filterwarnings("ignore") 

# Parcel level: load necessary Lidar
basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
# neighborhood = "HECAPO"
neighborhood = "Test_70_el Besòs i el Maresme"
parcelsFolder = basePath + "/Results/" + neighborhood + "/Parcels/"

lidarFolder = basePath + "RAW_Data/LiDAR/"

lidarCellsInfoFile = basePath + "Results/Test_70_el Besòs i el Maresme/necessaryLiDAR_Buffer100.txt"
# lidarCellsInfoFile = basePath + "Results/HECAPO/necessaryLiDAR_Buffer100.txt"
lidarInfoDF = pd.read_csv(lidarCellsInfoFile)
lidarInfoDF["files"] = lidarInfoDF["files"].apply(json.loads)
lidarInfoDF["bounds"] = lidarInfoDF["bounds"].apply(json.loads)
lidarInfoDF = lidarInfoDF.sort_values("files").reset_index(drop=True)


selectedParcels = lidarInfoDF[lidarInfoDF['REFCAT'].isin(os.listdir(parcelsFolder))].reset_index(drop=True)


def create_output_folder(directory, deleteFolder = False):
    if not(os.path.isdir(directory)):
        os.makedirs(directory)
    else:
        if(deleteFolder):
            shutil.rmtree(directory)
            os.makedirs(directory)

def load_necessary_laz(lidarFolder, fileList):
    lasDF_list = []
    for file in fileList:
        lasPath = lidarFolder + file + ".laz"
        lasDF = laspy.read(lasPath)
        lasDF_list.append(lasDF.xyz)

    lasCoords = np.concatenate(lasDF_list)
    return lasCoords

def getGrid(selectedCoords):
    spacing = 1
    region = pygmt.info(data=selectedCoords, spacing=spacing)
    df_trimmed = pygmt.blockmedian(data=selectedCoords, T=0.5, spacing = spacing, region = region)
    df_trimmed = df_trimmed.rename(columns={0:"x",1:"y",2:"z"})
    with open(os.devnull, 'w') as fnull, contextlib.redirect_stderr(fnull):
        grid = pygmt.surface(x=df_trimmed.x, y=df_trimmed.y, z=df_trimmed.z, spacing=spacing, region = region, tension = 0.35) #T: check bibliography

    x = grid.x.values
    y = grid.y.values
    Z = grid.values
    X, Y = np.meshgrid(x, y)

    return X, Y, Z

def sample_points(clusterPoints, cellSize = 0.75):
    grid = defaultdict(list)

    # Round points to the nearest integer for x and y
    for point in clusterPoints:
        x, y, z = point
        grid_cell = (round(x/cellSize)*cellSize, round(y/cellSize)*cellSize)
        grid[grid_cell].append(z)

    # Prepare the output as a reduced array with the average z-value for each grid cell
    reduced_array = []
    for grid_cell, z_values in grid.items():
        x, y = grid_cell
        avg_z = np.mean(z_values)  # Compute the average z-value for the grid cell
        reduced_array.append([x, y, avg_z])

    return reduced_array

def get_shading_profile(point, X, Y, Z):
    Z_point = point[2]+0.05
    
    azimuthAngle = np.zeros(X.shape)
    azimuthAngle = np.arctan2(X[:,:] - point[0], Y[:,:] - point[1])*180/math.pi
    azimuthAngle = np.where(azimuthAngle < 0, azimuthAngle + 360, azimuthAngle)
    azimuthAngle = np.round(azimuthAngle).astype(int)


    tiltangle = np.zeros(X.shape)
    # # This can be further optimized by applying a mask on the azimuth, but that means that the angles need to be handled in case there is a missing orientation
    # mask = (azimuthAngle >= 60) & (azimuthAngle <= 300) & (Z >= Z_point)
    # distance = np.sqrt((X[mask] - point[0])**2 + (Y[mask] - point[1])**2)
    # tiltangle[mask] = np.arctan2((Z[mask] - Z_point), distance) * 180 / math.pi

    distance = np.sqrt((X[:,:] - point[0])**2 + (Y[:,:] - point[1])**2)
    tiltangle = np.arctan2((Z[:,:] - Z_point), distance[:,:])*180/math.pi
    tiltangle = np.maximum(tiltangle, 0)

    azimuthAngle_flat = azimuthAngle.ravel()
    tiltangle_flat = tiltangle.ravel()
    df = pd.DataFrame({
        'azimuth': azimuthAngle_flat,
        'tiltangle': tiltangle_flat
    })

    max_tilt_df = df.groupby('azimuth')['tiltangle'].max().reset_index()
    max_tilt_df["tiltangle"] = max_tilt_df["tiltangle"].round()
    return max_tilt_df.tiltangle.values


previousFileList = []
for i in tqdm(range(len(selectedParcels)), desc="Looping through parcels", leave=True):
        parcel = selectedParcels.REFCAT[i]
    # if((parcel == "4054901DF3845C") or (parcel == "4649601DF3844H")):

        if(not np.array_equal(previousFileList, selectedParcels.files[i])):
            lasCoords = load_necessary_laz(lidarFolder, selectedParcels.files[i])
            previousFileList = selectedParcels.files[i]

        bounds = selectedParcels.bounds[i]
        selectedCoords = lasCoords[np.where((lasCoords[:,0] > bounds[0]) & (lasCoords[:,1] > bounds[1]) & (lasCoords[:,0] < bounds[2]) & (lasCoords[:,1] < bounds[3]))]

        X, Y, Z = getGrid(selectedCoords)

        
        parcelSubfolder = parcelsFolder + parcel + "/"

        for construction in tqdm([x for x in os.listdir(parcelSubfolder) if os.path.isdir(parcelSubfolder + x)],  desc="Working on constructions", leave=True):
            # if((construction == "242") or (construction == "342") or (construction == "550") or (construction == "557")):
            # if((construction == "408") or (construction == "86")):
                try:
                    constructionFolder = parcelSubfolder + construction
                    
                    constructionFile = constructionFolder + "/Plane Identification/"+ construction+".gpkg"
                    planesGDF = gpd.read_file(constructionFile)
                    lasFile = constructionFolder + "/Plane Identification/"+ construction +".laz"
                    lasDF = laspy.read(lasFile)
                    
                    create_output_folder(constructionFolder + "/Shading/", deleteFolder=True)
                    
                    for cluster in tqdm(planesGDF.cluster.values, desc="Doing all clusters", leave=False):
                        geometry = planesGDF[planesGDF.cluster == cluster].geometry.values
                        area = geometry.area

                        clusterPoints = lasDF[lasDF.classification == cluster]
                        clusterPoints = clusterPoints.xyz
                        selectedPoints = sample_points(clusterPoints, cellSize=1)    
                        shapely_points = [Point(p[:2]) for p in selectedPoints]
                        inside_points = [point for point, shapely_point in zip(selectedPoints, shapely_points) if geometry.contains(shapely_point)]            

                        shading_results = []
                        for idx, point in enumerate(tqdm(inside_points, desc="Processing points", leave=False)):
                            shading_results.append(get_shading_profile(point, X, Y, Z))

                        combined_array = np.hstack((inside_points, shading_results))
                        exportFile = constructionFolder + "/Shading/" + str(cluster) + ".csv"
                        np.savetxt(exportFile, combined_array, delimiter=",", fmt="%.2f")
                except Exception as e:
                    print(" ", parcel, construction, " ", e)