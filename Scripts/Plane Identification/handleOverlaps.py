from sklearn.linear_model import LinearRegression
import geopandas as gpd
from shapely.ops import unary_union
from shapely.geometry import Polygon, MultiPolygon, GeometryCollection, Point, MultiPoint
from shapely.affinity import rotate
import math

from tqdm import tqdm
import pandas as pd
import numpy as np
import os
import shutil
import csv
import time
from scipy.spatial import ConvexHull

def create_output_folder(directory, deleteFolder = False):
    if not(os.path.isdir(directory)):
        os.makedirs(directory)
    else:
        if(deleteFolder):
            shutil.rmtree(directory)
            os.makedirs(directory)

def handle_overlaps(constructionFolder, deleteThresholdArea = 0.5):
    start = time.time()

    inputFolder = constructionFolder + "/Plane Processing/Cadaster Fitting/"
    outputFolder = constructionFolder + "/Plane Processing/No Overlaps/"
    create_output_folder(outputFolder + "/Plane Lists/", deleteFolder=True)
    create_output_folder(outputFolder + "/Plane Points/", deleteFolder=True)
    create_output_folder(outputFolder + "/Geopackages/", deleteFolder=True)

    # Read all data
    planeListFiles = os.listdir(inputFolder + "/Plane Lists/")
    planeListFiles.sort(reverse=True)

    allPlaneLists = []
    allPlanePoints = []
    allGDFs = []
    allPlaneIDs = []

    for planeFile in planeListFiles:
        heightGroup = planeFile.replace(".csv", "")
        planeLists = []
        planePoints = []
        gdfList = []
        planeIDList = []
        
        for file in [file for file in os.listdir(inputFolder + "/Plane Points/") if file.startswith(heightGroup)]:
            planeIDList.append(file.replace(".csv", ""))
            fileName = inputFolder + "/Plane Points/" + file
            if os.stat(fileName).st_size > 0:
                df = pd.read_csv(fileName, header=None)
                df = df.rename(columns={0:'x', 1:'y', 2:'z'})
                planePoints.append(df)

            lm = LinearRegression()
            lm.fit(df[["x", "y"]], df.z)
            planeLists.append([lm.coef_[0], lm.coef_[1], -1, lm.intercept_])
            gdfList.append(gpd.read_file(inputFolder + "/Geopackages/" + file.replace(".csv", ".gpkg")).union_all())

        if(len(gdfList) > 0):
            allPlaneLists.append(planeLists)
            allPlanePoints.append(planePoints)
            allGDFs.append(gdfList)
            allPlaneIDs.append(planeIDList)
    
    #############################################################
    # Overlap from higher planes
    masksList = []

    for gdfList in allGDFs[:-1]:
        mask = unary_union(gdfList)
        masksList.append(mask)

    # This is done this way, because else there could be linestrings generated
    for i in range(1,len(masksList)-1):
        masksList[i] = unary_union([masksList[i-1], masksList[i]])

    for i in range(1, len(allGDFs)):
        for j in range(len(allGDFs[i])):
            allGDFs[i][j] = allGDFs[i][j].difference(masksList[i-1])

    exportPlaneLists = []
    exportPlanePoints = []
    exportGDFs = []

    for i in range(len(allGDFs)):
        for j in range(len(allGDFs[i])):
            if(allGDFs[i][j].area > deleteThresholdArea):
                exportPlaneLists.append(allPlaneLists[i][j])
                exportPlanePoints.append(allPlanePoints[i][j])
                exportGDFs.append(allGDFs[i][j])
                



    # Save final plane lists and planePoints
    with open(outputFolder + "/Plane Lists/PlaneList.csv", "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerows(exportPlaneLists)

    for i in range(len(exportPlanePoints)):
        filename = outputFolder + "/Plane Points/" + str(i) + ".csv" #str(i).zfill(2)
        exportPlanePoints[i][["x", "y", "z"]].to_csv(filename, header=None, index=False)            

    for i in range(len(exportGDFs)):
        gdf = gpd.GeoDataFrame(geometry=[exportGDFs[i]], crs="EPSG:25831")
        filename = outputFolder + "/Geopackages/" + str(i) + ".gpkg"
        gdf.to_file(filename, driver="GPKG")

    finish = time.time()

    # Metrics
    elapsed_time = finish-start
    return elapsed_time

if __name__ == "__main__":
    basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
    neighborhood = "70_el Besòs i el Maresme"
    parcelsFolder = basePath + "/Results/" + neighborhood + "/Parcels/"

    parcelsList = []
    constructionsList = []
    elapsedTimesList = []
    for parcel in tqdm(os.listdir(parcelsFolder)):
        parcelPath = parcelsFolder + parcel
        for construction in [x for x in os.listdir(parcelPath) if os.path.isdir(parcelPath + "/" + x)]:
            constructionFolder = parcelPath + "/" + construction + "/"
            try:
                elapsed_time = handle_overlaps(constructionFolder)
                elapsedTimesList.append(elapsed_time)
                parcelsList.append(parcel)
                constructionsList.append(construction)

            except Exception as e:
                print(parcel, construction, e)

    summaryDF = pd.DataFrame({
    'parcel': parcelsList,
    'construction': constructionsList,
    'time': elapsedTimesList
    })

    print(summaryDF.head())