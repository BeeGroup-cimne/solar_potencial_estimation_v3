from sklearn.linear_model import LinearRegression
import geopandas as gpd
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

def fit_cadaster(constructionFolder):
    start = time.time()

    inputFolder = constructionFolder + "/Plane Processing/Plane Deleting/"
    outputFolder = constructionFolder + "/Plane Processing/Cadaster Fitting/"
    create_output_folder(outputFolder + "/Plane Lists/", deleteFolder=True)
    create_output_folder(outputFolder + "/Plane Points/", deleteFolder=True)
    create_output_folder(outputFolder + "/Geopackages/", deleteFolder=True)

    gpkg_file = [f for f in os.listdir(constructionFolder + "/Map files/" ) if f.endswith(".gpkg")][0]
    cadasterGDF = gpd.read_file(constructionFolder + "/Map files/" + gpkg_file).union_all()
    rotated_bounding_box = cadasterGDF.minimum_rotated_rectangle
    bbox_coords = list(rotated_bounding_box.exterior.coords)
    bottom_left, top_left = bbox_coords[0], bbox_coords[1]
    dx, dy = top_left[0] - bottom_left[0], top_left[1] - bottom_left[1]
    rotation_angle = math.atan2(dy, dx) #math.degrees() for debugging purposes

    for planeListFile in os.listdir(inputFolder + "/Plane Lists/"):
        heightGroup = planeListFile.replace(".csv", "")
        planeLists = []
        planePoints = []
        for file in [file for file in os.listdir(inputFolder + "/Plane Points/") if file.startswith(heightGroup)]:
            fileName = inputFolder + "/Plane Points/" + file
            if os.stat(fileName).st_size > 0:
                df = pd.read_csv(fileName, header=None)
                df = df.rename(columns={0:'x', 1:'y', 2:'z'})
                planePoints.append(df)

            lm = LinearRegression()
            lm.fit(df[["x", "y"]], df.z)
            planeLists.append([lm.coef_[0], lm.coef_[1], -1, lm.intercept_])

        # Come on, do something
        gdfList = []
        for pointsDF in planePoints:
            points = [Point(x, y) for x, y in zip(pointsDF['x'], pointsDF['y'])]
            multi_point = MultiPoint(points)
            rotated_bbox = multi_point.minimum_rotated_rectangle

            gdf_clipped = gpd.GeoDataFrame(geometry=[rotated_bbox], crs="EPSG:25831").clip(cadasterGDF)
            gdfList.append(gdf_clipped)
        
        # Export geopackages
        for i in range(len(gdfList)):
            processed_geoms = []
            for geom in gdfList[i].geometry:
                if geom.geom_type == 'GeometryCollection':
                    # Extract only Polygon and MultiPolygon parts from GeometryCollection
                    polygons = [part for part in geom.geoms if isinstance(part, (Polygon, MultiPolygon))]
                    if polygons:
                        # Convert to MultiPolygon if more than one polygonal part, otherwise keep as Polygon
                        processed_geoms.append(MultiPolygon(polygons) if len(polygons) > 1 else polygons[0])
                elif isinstance(geom, (Polygon, MultiPolygon)):
                    processed_geoms.append(geom)

                if processed_geoms:
                    gdf_save = gpd.GeoSeries(processed_geoms, crs="EPSG:25831")
                    filename = outputFolder + "/Geopackages/" + heightGroup + "_" + str(i) + ".gpkg"
                    gdf_save.to_file(filename, driver="GPKG")


        # Save final plane lists and planePoints
        with open(outputFolder + "/Plane Lists/" + heightGroup + ".csv", "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerows(planeLists)

        for i in range(len(planePoints)):
            filename = outputFolder + "/Plane Points/" + heightGroup + "_" + str(i) + ".csv" #str(i).zfill(2)
            planePoints[i][["x", "y", "z"]].to_csv(filename, header=None, index=False)            

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
                elapsed_time = fit_cadaster(constructionFolder)
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