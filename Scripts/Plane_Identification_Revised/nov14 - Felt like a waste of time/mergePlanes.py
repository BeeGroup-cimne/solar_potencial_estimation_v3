from sklearn.linear_model import LinearRegression
from tqdm import tqdm
import pandas as pd
import numpy as np
import os
import math
import csv
import shutil
import time


def create_output_folder(directory, deleteFolder = False):
    if not(os.path.isdir(directory)):
        os.makedirs(directory)
    else:
        if(deleteFolder):
            shutil.rmtree(directory)
            os.makedirs(directory)

def fillMatrix(planeLists, planePoints):
    distanceMatrix = np.empty((len(planeLists), len(planeLists)))
    angleMatrix = np.empty((len(planeLists), len(planeLists)))

    for i in range(len(planeLists)):
        for j in range(len(planeLists)):
            if i == j:
                distanceMatrix[i][j] = 0
                angleMatrix[i][j] = 0
            else:
                distanceMatrix[i][j] = planePointDistance(planePoints[i], planeLists[j])
            
            if j < i:
                angle = planeAngle(planeLists[i], planeLists[j])
                angleMatrix[i][j] = angle
                angleMatrix[j][i] = angle
    
    return distanceMatrix, angleMatrix

def planePointDistance(planePoints, plane):
    A, B, C, D = plane[0], plane[1], plane[2], plane[3]
    distance = np.mean(abs(A*planePoints.x+ B*planePoints.y + C*planePoints.z + D) / math.sqrt(A**2 + B**2 + C**2))
    return distance

def planeAngle(plane1, plane2):
    A1, B1, C1 = plane1[0], plane1[1], plane1[2]
    A2, B2, C2 = plane2[0], plane2[1], plane2[2]
    cosPhi = (A1*A2+B1*B2+C1*C2)/(math.sqrt(A1**2+B1**2+C1**2)*math.sqrt(A2**2+B2**2+C2**2))
    phi = np.arccos(cosPhi)*180/np.pi
    return phi

def canSimplify(distanceMatrix, angleMatrix, distanceThreshold=0.15, angleThreshold=5):
    coordinates = [-1, -1]
    for i in range(len(distanceMatrix)):
        for j in range(len(distanceMatrix)):
            if i != j:
                if(distanceMatrix[i][j] <= distanceThreshold) and (angleMatrix[i][j] <= angleThreshold):
                    return [i,j]
    return coordinates

def deletePositions(planePoints, planeLists, i, j):
    if i>j:
        planePoints.pop(i)
        planePoints.pop(j)  
        planeLists.pop(i) 
        planeLists.pop(j)
    else:
        planePoints.pop(j)
        planePoints.pop(i)  
        planeLists.pop(j) 
        planeLists.pop(i)
    
    return planePoints, planeLists


def merge_planes(constructionFolder):
    start = time.time()

    inputFolder = constructionFolder + "/Plane Identification/"
    create_output_folder(constructionFolder + "/Plane Processing/", deleteFolder=True)
    outputFolder = constructionFolder + "/Plane Processing/Plane Merging/"
    create_output_folder(outputFolder + "/Plane Lists/", deleteFolder=True)
    create_output_folder(outputFolder + "/Plane Points/", deleteFolder=True)

    for planeListFile in os.listdir(inputFolder + "/Plane Lists/"):
        heightGroup = planeListFile.replace(".csv", "")
        planeLists = []
        planePoints = []

        for file in  [file for file in os.listdir(inputFolder + "/Plane Points/") if file.startswith(heightGroup)]:
            df = pd.read_csv(inputFolder + "/Plane Points/" + file, header=None)
            df = df.rename(columns={0:'x', 1:'y', 2:'z'})
            planePoints.append(df)

            lm = LinearRegression()
            lm.fit(df[["x", "y"]], df.z)
            planeLists.append([lm.coef_[0], lm.coef_[1], -1, lm.intercept_])

        # Get a matrix of all plane distances and angles:
        distanceMatrix, angleMatrix = fillMatrix(planeLists, planePoints)
     
        simplifyPos = canSimplify(distanceMatrix, angleMatrix)
        while(simplifyPos[0] != -1):
            i, j = simplifyPos[0], simplifyPos[1]
            
            df = pd.concat([planePoints[i], planePoints[j]])
            planePoints.append(df)
            lm = LinearRegression()
            lm.fit(df[["x", "y"]], df.z)
            planeLists.append([lm.coef_[0], lm.coef_[1], -1, lm.intercept_])
            
            planePoints, planeLists = deletePositions(planePoints, planeLists, i, j)
        
            distanceMatrix, angleMatrix = fillMatrix(planeLists, planePoints)
            simplifyPos = canSimplify(distanceMatrix, angleMatrix)

        # #########################

        for i in range(len(planeLists)):
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
    neighborhood = "Test_70_el Besòs i el Maresme"
    parcelsFolder = basePath + "/Results/" + neighborhood + "/Parcels/"

    parcelsList = []
    constructionsList = []
    elapsedTimesList = []
    for parcel in tqdm(os.listdir(parcelsFolder)):
        parcelPath = parcelsFolder + parcel
        for construction in [x for x in os.listdir(parcelPath) if os.path.isdir(parcelPath + "/" + x)]:
            constructionFolder = parcelPath + "/" + construction + "/"
            try:
                elapsed_time = merge_planes(constructionFolder)
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