import os
import shutil
from tqdm import tqdm
import pandas as pd
import laspy
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import root_mean_squared_error
import csv
import time
from Scripts.Plane_Identification_Revised.planeIDalgs.simpleRansac import ransacHeightSplit
import warnings
warnings.filterwarnings('ignore')




#### Working code

def create_output_folder(directory, deleteFolder = False):
    if not(os.path.isdir(directory)):
        os.makedirs(directory)
    else:
        if(deleteFolder):
            shutil.rmtree(directory)
            os.makedirs(directory)

def compute_accuracy(planes, pointsPlanes):
    z_actual = []
    z_predicted = []
    
    for i in range(len(planes)):
        if isinstance(planes[i], list):
            for j in range(len(planes[i])):
                a, b, d = planes[i][j][0], planes[i][j][1], planes[i][j][3]
                z_actual.extend(pointsPlanes[i][j].z)
                z_predicted.extend(pointsPlanes[i][j].x * a + pointsPlanes[i][j].y * b + d)
        else:
            a, b, d = planes[i][0], planes[i][1], planes[i][3]
            z_actual.extend(pointsPlanes[i].z)
            z_predicted.extend(pointsPlanes[i].x * a + pointsPlanes[i].y * b + d)

    rmse = root_mean_squared_error(np.array(z_actual), np.array(z_predicted))
    return rmse

def detect_planes(buildingsFolder):
    start = time.time()

    outputFolder = buildingsFolder + "/Plane Identification/"
    create_output_folder(outputFolder, deleteFolder = True)
    planeListFolder = outputFolder + "/Plane Lists/"
    planePointsFolder = outputFolder + "/Plane Points/"
    create_output_folder(planeListFolder)
    create_output_folder(planePointsFolder)

    lazPath = [x for x in os.listdir(buildingsFolder + "/Map files/") if x.endswith(".laz")][0]
    lazPath = buildingsFolder + "/Map files/" + lazPath
    lazFile = laspy.read(lazPath)
    xyz = lazFile.xyz

    lasDF = pd.DataFrame(xyz, columns=['x', 'y', 'z'])
    lasDF['r'] = lazFile.red/65535.0# Step 1: Create a template for custom clustering algorithms
    # Apply the algorithm
    planes, pointsPlanes = ransacHeightSplit(lasDF)

    # Write the Damn CSVs
    for i in range(len(planes)):
        with open(planeListFolder + str(i), "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerows(planes[i])

        for j in range(len(pointsPlanes[i])):
            filename = planePointsFolder + str(i) + "_" + str(j) + ".csv"
            pointsPlanes[i][j][["x", "y", "z"]].to_csv(filename, header=None, index=False)

    finish = time.time()

    # Metrics
    accuracy = compute_accuracy(planes, pointsPlanes)
    elapsed_time = finish-start
    total_planes = sum([len(heightGroup) for heightGroup in planes])
    sampledPoints = sum([len(pointsInPlane) for heightGroup in pointsPlanes for pointsInPlane in heightGroup])
    unidentifiedPoints = len(lasDF) - sampledPoints
    return len(lasDF), total_planes, unidentifiedPoints, elapsed_time, accuracy

if __name__ == "__main__":
    basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
    neighborhood = "Test_70_el Besòs i el Maresme"
    parcelsFolder = basePath + "/Results/" + neighborhood + "/Parcels/"
    parcelsList = []
    constructionsList = []
    totalPointsList = []
    totalPlanesList = []
    unidentifiedPointsList = []
    elapsedTimesList = []
    accuraciesList = []

    for parcel in tqdm(os.listdir(parcelsFolder)):
        parcelPath = parcelsFolder + parcel
        for construction in [x for x in os.listdir(parcelPath) if os.path.isdir(parcelPath + "/" + x)]:
            constructionFolder = parcelPath + "/" + construction + "/"
            try:
                pointCount, planesCount, unidentifiedCount, timeDiff, score = detect_planes(constructionFolder)
                
                parcelsList.append(parcel)
                constructionsList.append(construction)
                totalPointsList.append(pointCount)
                totalPlanesList.append(planesCount)
                unidentifiedPointsList.append(unidentifiedCount)
                elapsedTimesList.append(timeDiff)
                accuraciesList.append(score)
            except Exception as e:
                print(parcel, construction, e)
                parcelsList.append(parcel)
                constructionsList.append(construction)
                totalPointsList.append(e)
                totalPlanesList.append(0)
                unidentifiedPointsList.append(0)
                elapsedTimesList.append(0)
                accuraciesList.append(0)
    
    summaryDF = pd.DataFrame({
        'parcel': parcelsList,
        'construction': constructionsList,
        'pointsCount': totalPointsList,
        'planeCount': totalPlanesList,
        'unidentifiedPoints': unidentifiedPointsList,
        'time': elapsedTimesList,
        'accuracy': accuraciesList
        })
    
    summaryDF.to_csv(basePath + "/Results/" + neighborhood + "/Identification report.csv", index=False)
    # detect_planes(buildingsFolder)