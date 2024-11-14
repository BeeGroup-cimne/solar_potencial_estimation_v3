from sklearn.linear_model import LinearRegression
from scipy.spatial import ConvexHull
from shapely import Polygon

from tqdm import tqdm
import pandas as pd
import numpy as np
import os
import shutil
import csv
import time

def create_output_folder(directory, deleteFolder = False):
    if not(os.path.isdir(directory)):
        os.makedirs(directory)
    else:
        if(deleteFolder):
            shutil.rmtree(directory)
            os.makedirs(directory)

def isPlaneTooSmall(pointsInPlane, threshold=2):
    x = pointsInPlane.x
    y = pointsInPlane.y
    
    p = []
    for j in range(len(x)):
        p.append((x[j], y[j]))

    p = np.array(p)
    hull = ConvexHull(p)
    outline = p[hull.vertices,:]

    polygon = Polygon(outline)
    area = polygon.area

    if(area < threshold):
        return True
    return False


def tooFewPoints(pointsInPlane, threshold=3):
    if(len(pointsInPlane) <= threshold):
        return True
    return False

def delete_planes(constructionFolder):
    start = time.time()

    inputFolder = constructionFolder + "/Plane Processing/Plane Splitting/"
    outputFolder = constructionFolder + "/Plane Processing/Plane Deleting/"
    create_output_folder(outputFolder + "/Plane Lists/", deleteFolder=True)
    create_output_folder(outputFolder + "/Plane Points/", deleteFolder=True)
    create_output_folder(outputFolder + "/Deleted Points/", deleteFolder=True)

    for planeListFile in os.listdir(inputFolder + "/Plane Lists/"):
        heightGroup = planeListFile.replace(".csv", "")
        planeLists = []
        planePoints = []
        deletedPlanePoints = []
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
        toDelete = []
        for i in range(len(planePoints)):
            if(tooFewPoints(planePoints[i])):
                toDelete.append(i)
            elif(isPlaneTooSmall(planePoints[i])):
                toDelete.append(i)
            
        toDelete.sort(reverse = True)
        for i in toDelete:
            deletedPlanePoints.append(planePoints[i])
            planePoints.pop(i)
            planeLists.pop(i)

        # Save final plane lists and planePoints
        with open(outputFolder + "/Plane Lists/" + heightGroup + ".csv", "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerows(planeLists)

        for i in range(len(planePoints)):
            filename = outputFolder + "/Plane Points/" + heightGroup + "_" + str(i) + ".csv" #str(i).zfill(2)
            planePoints[i][["x", "y", "z"]].to_csv(filename, header=None, index=False)

        for i in range(len(deletedPlanePoints)):
            filename = outputFolder + "/Deleted Points/" + heightGroup + "_" + str(i) + ".csv" #str(i).zfill(2)
            deletedPlanePoints[i][["x", "y", "z"]].to_csv(filename, header=None, index=False)
            

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
                elapsed_time = delete_planes(constructionFolder)
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