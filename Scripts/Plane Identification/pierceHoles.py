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

def obtainSquare(point, corner, vector1, vector2):
    A = np.array([[vector1[0], vector2[0]],[vector1[1], vector2[1]]])
    B = np.array([point[0] - point[0], point[1] - point[1]])
    n1, n2 = np.linalg.solve(A, B)
    trimBox = Polygon([corner, corner + n1*vector1, corner + n1*vector1 + n2*vector2, corner+ n2*vector2, corner])
    return trimBox

def pierce_holes(constructionFolder, areaThreshold = 2, sideThreshold=0.25):
    start = time.time()

    inputFolder = constructionFolder + "/Plane Processing/No Overlaps/"
    outputFolder = constructionFolder + "/Plane Processing/Piercing Holes/"
    create_output_folder(outputFolder + "/Plane Lists/", deleteFolder=True)
    create_output_folder(outputFolder + "/Plane Points/", deleteFolder=True)
    create_output_folder(outputFolder + "/Geopackages/", deleteFolder=True)

    gpkg_file = [f for f in os.listdir(constructionFolder + "/Map files/" ) if f.endswith(".gpkg")][0]
    cadasterGDF = gpd.read_file(constructionFolder + "/Map files/" + gpkg_file).union_all()
    rotated_bounding_box = cadasterGDF.minimum_rotated_rectangle

    planeLists = []
    planePoints = []
    gdfList = []
    for file in os.listdir(inputFolder + "/Plane Points/"):
        fileName = inputFolder + "/Plane Points/" + file
        if os.stat(fileName).st_size > 0:
            df = pd.read_csv(fileName, header=None)
            df = df.rename(columns={0:'x', 1:'y', 2:'z'})
            planePoints.append(df)

        lm = LinearRegression()
        lm.fit(df[["x", "y"]], df.z)
        planeLists.append([lm.coef_[0], lm.coef_[1], -1, lm.intercept_])

        gdfList.append(gpd.read_file(inputFolder + "/Geopackages/" + file.replace(".csv", ".gpkg")).union_all())


    # Come on, do something
    for i in range(len(gdfList)):
        currentGDF = gdfList[i]
        pointsPlane = planePoints[i].copy()
        vertices = list(currentGDF.exterior.coords)
        
        # bbox = currentGDF.minimum_rotated_rectangle
        # bbox_coords = list(bbox.exterior.coords)
        # bottom_left, top_left = bbox_coords[0], bbox_coords[1]
        # dx, dy = top_left[0] - bottom_left[0], top_left[1] - bottom_left[1]
        # rotation_angle = math.atan2(dy, dx) #math.degrees() for debugging purposes

        for j in range(len(vertices)-1):
            currentPoint = vertices[j]
            previousPoint = vertices[j-1 if (j-1) > 0 else -2]
            nextPoint = vertices[j+1]
            vector1 = [previousPoint[0] - currentPoint[0], previousPoint[1] - currentPoint[1]]
            vector2 = [nextPoint[0] - currentPoint[0], nextPoint[1] - currentPoint[1]]
            
            vector1 = np.array(vector1)
            vector2 = np.array(vector2)

            vector1 = vector1 / np.sqrt(vector1[0]**2 + vector1[1]**2)
            vector2 = vector2 / np.sqrt(vector2[0]**2 + vector2[1]**2)

            dot_product = np.dot(vector1, vector2)
            magnitude_v1 = np.linalg.norm(vector1)
            magnitude_v2 = np.linalg.norm(vector2)
            cos_theta = dot_product / (magnitude_v1 * magnitude_v2)
            angle_rad = np.arccos(np.clip(cos_theta, -1.0, 1.0))  # Clip to avoid numerical issues
            angle_deg = np.degrees(angle_rad)
            print(angle_deg)
            # if(angle_deg < 95):
            #     displacements = pointsPlane[['x', 'y']].values - currentPoint
            #     distance1 = np.dot(displacements, vector1)
            #     distance2 = np.dot(displacements, vector2)
            #     pointsPlane['distance1'] = distance1
            #     pointsPlane['distance2'] = distance2

            #     positive_distances = pointsPlane[(pointsPlane['distance1'] > 0) & (pointsPlane['distance2'] > 0)]
            #     print(len(positive_distances))
            #     points = positive_distances[['x', 'y']].values  # Get the points as a numpy array
            #     hull = ConvexHull(points)  # Compute the convex hull
            #     hull_indices = hull.vertices  # Indices of the vertices that form the convex hull
            #     min_d1_idx = positive_distances["distance1"].idxmin()
            #     min_d2_idx = positive_distances["distance2"].idxmin()
            #     # Get the maximum of each distance and the corresponding other distance
            #     maxd1 = positive_distances.loc[min_d2_idx, "distance1"]
            #     maxd2 = positive_distances.loc[min_d1_idx, "distance2"]

            #     print(maxd1, maxd2)
            #     on_convex_hull = positive_distances[(positive_distances.index.isin(hull_indices))]
            #     # on_convex_hull['square'] = on_convex_hull.apply(lambda row: obtainSquare(np.array([row['x'], row['y']]), currentPoint, vector1, vector2), axis=1)
            #     print(on_convex_hull)
            #     # # Find the index of the row with the minimum distance
            #     # closest_points = []
            #     # positive_distances = pointsPlane[(pointsPlane['distance1'] > 0) & (pointsPlane['distance2'] > 0)]
            #     # if not positive_distances.empty:
            #     #     closest_point_index = positive_distances['distance1'].idxmin()
            #     #     closest_points.append([pointsPlane.loc[closest_point_index, ['x', 'y']]["x"], pointsPlane.loc[closest_point_index, ['x', 'y']]["y"]])
            #     # if not positive_distances.empty:
            #     #     closest_point_index = positive_distances['distance2'].idxmin()
            #     #     closest_points.append([pointsPlane.loc[closest_point_index, ['x', 'y']]["x"], pointsPlane.loc[closest_point_index, ['x', 'y']]["y"]])
                
            #     # for closest_point in closest_points:
            #     #     A = np.array([[vector1[0], vector2[0]],[vector1[1], vector2[1]]])
            #     #     B = np.array([closest_point[0] - currentPoint[0], closest_point[1] - currentPoint[1]])
            #     #     n1, n2 = np.linalg.solve(A, B)
            #     #     print(n1, n2)
            #     #     if(n1 > sideThreshold and n2 > sideThreshold):
            #     #         currentPoint = np.array(currentPoint)
            #     #         closest_point = np.array(closest_point)
            #     #         trimBox = Polygon([currentPoint, currentPoint + n1*vector1, currentPoint + n1*vector1 + n2*vector2, currentPoint+ n2*vector2, currentPoint])
            #     #         if (trimBox.area > areaThreshold):
            #     #             print(currentPoint, trimBox.area)
            #     #             gdfList[i] = gdfList[i].difference(trimBox)

    # Export geopackages
    # for i in range(len(gdfList)):
    #     gdf_save = gpd.GeoSeries(gdfList[i], crs="EPSG:25831")
    #     filename = outputFolder + "/Geopackages/" + str(i) + ".gpkg"
    #     gdf_save.to_file(filename, driver="GPKG")


    #     # Save final plane lists and planePoints
    #     with open(outputFolder + "/Plane Lists/" + heightGroup + ".csv", "w", newline='') as f:
    #         writer = csv.writer(f)
    #         writer.writerows(planeLists)

    #     for i in range(len(planePoints)):
    #         filename = outputFolder + "/Plane Points/" + heightGroup + "_" + str(i) + ".csv" #str(i).zfill(2)
    #         planePoints[i][["x", "y", "z"]].to_csv(filename, header=None, index=False)            

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
    # for parcel in tqdm(os.listdir(parcelsFolder)[0:1]):
    for parcel in ["4054901DF3845C"]:
        parcelPath = parcelsFolder + parcel
        for construction in [x for x in os.listdir(parcelPath) if os.path.isdir(parcelPath + "/" + x)]:
            constructionFolder = parcelPath + "/" + construction + "/"
            try:
                elapsed_time = pierce_holes(constructionFolder)
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