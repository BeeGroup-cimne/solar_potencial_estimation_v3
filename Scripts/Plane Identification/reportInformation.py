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
from guidedRansac import *
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

def compute_accuracy(planes, pointsPlanes):
    z_actual = []
    z_predicted = []
    for i in range(len(planes)):
        for j in range(len(planes[i])):
            a, b, d = planes[i][j][0], planes[i][j][1], planes[i][j][3]
            z_actual = pointsPlanes[i][j].z
            z_predicted = pointsPlanes[i][j].x*a + pointsPlanes[i][j].y*b + d

    rmse = root_mean_squared_error(z_actual, z_predicted)
    return rmse

def obtain_accuracy(constructionFolder, subfolder):
    start = time.time()

    inputFolder = constructionFolder + subfolder

    planes = []
    pointsPlanes = []
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

        planes.append(planeLists)
        pointsPlanes.append(planePoints)

    finish = time.time()

    # Metrics
    accuracy = compute_accuracy(planes, pointsPlanes)
    return accuracy

if __name__ == "__main__":
    basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
    neighborhood = "70_el Besòs i el Maresme"
    subfolder = "/Plane Processing/Cadaster Fitting/"
    parcelsFolder = basePath + "/Results/" + neighborhood + "/Parcels/"

    parcelsList = []
    constructionsList = []
    accuracyList = []
    for parcel in tqdm(os.listdir(parcelsFolder)):
        parcelPath = parcelsFolder + parcel
        for construction in [x for x in os.listdir(parcelPath) if os.path.isdir(parcelPath + "/" + x)]:
            constructionFolder = parcelPath + "/" + construction + "/"
            try:
                accuracy = obtain_accuracy(constructionFolder, subfolder)
                accuracyList.append(accuracy)
                parcelsList.append(parcel)
                constructionsList.append(construction)
            except Exception as e:
                pass 
                # print(parcel, construction, e)

    summaryDF = pd.DataFrame({
        'parcel': parcelsList,
        'construction': constructionsList,
        'accuracy': accuracyList
    })

    print(summaryDF.head())