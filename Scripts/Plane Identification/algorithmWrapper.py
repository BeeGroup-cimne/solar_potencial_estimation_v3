import os
import shutil
import tqdm
import pandas as pd
import laspy
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import root_mean_squared_error
import csv
import time
from guidedRansac import *
import warnings
warnings.filterwarnings('ignore')


### Algorithms

def sampleAlgorithm(lasDF): # This is just to have a sample interface, this particular algorithm does not makes a lot of sense
    remainingPoints = lasDF.sample(frac=0.1, random_state=42)  # Adjust frac to desired percentage
    lasDF_no_remaining = lasDF.drop(remainingPoints.index)
    
    lm = LinearRegression()
    
    pointsPlane1 = lasDF_no_remaining[lasDF_no_remaining.z > np.mean(lasDF_no_remaining.z)]
    pointsPlane2 = lasDF_no_remaining[lasDF_no_remaining.z <= np.mean(lasDF_no_remaining.z)]
    
    lm.fit(pointsPlane1[["x", "y"]], pointsPlane1.z)
    plane1 = [lm.coef_[0], lm.coef_[1], -1, lm.intercept_]
    lm.fit(pointsPlane2[["x", "y"]], pointsPlane2.z)
    plane2 = [lm.coef_[0], lm.coef_[1], -1, lm.intercept_]
    
    planes = [[plane1], [plane2]]
    pointsPlanes = [[pointsPlane1], [pointsPlane2]]

    return planes, pointsPlanes

""" 
def ransacSimple(lasDF, stoppingPercentage = 0.2):
    def __heightSplit(lasDF, heightThreshold = 0.45, filter = True):
        newdf = lasDF.copy().sort_values("z").reset_index(drop=True)
        newdf["deltaZ"] = np.concatenate(([0], newdf.z[1:len(lasDF)].values - newdf.z[0:len(lasDF)-1].values))

        heightGroups = []
        lastSplit = 0

        for i in range(1,len(newdf)):
            if(newdf.deltaZ[i] > heightThreshold):
                heightGroups.append(newdf.iloc[lastSplit:i])
                lastSplit = i

        # Append "final group"
        if(lastSplit != i):
            heightGroups.append(newdf.iloc[lastSplit:i])
            
        # Filter, if wanted
        if(not filter): 
            return heightGroups

        else:
            filteredHeightGroups = heightGroups.copy()
            
            toDelete = []

            # We delete all those with 3 points or less
            for x in range(len(filteredHeightGroups)):
                if(len(filteredHeightGroups[x]) <= 3):
                    toDelete.append(x)

            toDelete.reverse() #Change order so it deletes last groups first (thus indexes are not modified during the process)
            for x in toDelete:
                del filteredHeightGroups[x]

            return filteredHeightGroups
        
    def __distancePlane(point, planeParams):
        a, b, c, d = planeParams[0], planeParams[1], planeParams[2], planeParams[3]
        x, y, z = point[0], point[1], point[2]
        dis = a*x + b*y + c*z+ d
        return abs(dis)
    
    def __ransac(pointsdf, minPoints  = 3, distanceThreshold = 0.45, ransacIterations = 20):
        bestPlane = []
        bestScore = 0
        bestPointsInPlane = []
        for i in range(ransacIterations):
            toFit = pointsdf.sample(n=3)
            # Fit a plane with these n random points 
            X = toFit[["x", "y"]].values
            y = toFit[["z"]].values
            
            model = LinearRegression().fit(X, y)
            plane = model.coef_[0][0], model.coef_[0][1], -1, model.intercept_[0]
            
            pointsInPlane = []
            # Check for all points in the dataset that can belong to this plane (distance below threshold)
            for j in range(len(pointsdf)):
                point = pointsdf[["x", "y", "z"]].iloc[j]
                pointsdf.loc[j, "dist"] = __distancePlane(point, plane)
                if(pointsdf.loc[j, "dist"] < distanceThreshold):
                    pointsInPlane.append(j)

            planePoints = pointsdf[["x", "y", "z", "dist"]].iloc[pointsInPlane]

            if(len(planePoints) > minPoints):
                z_actual = planePoints.z
                a, b, d = plane[0], plane[1], plane[3]
                z_predicted = planePoints.x*a + planePoints.y*b + d

                newScore = root_mean_squared_error(z_actual, z_predicted)

                if(newScore < bestScore):
                    bestPointsInPlane = pointsInPlane
                    bestPlane = plane
                    bestScore = newScore
            
            planePoints = pointsdf.copy().loc[pointsdf.index.isin(bestPointsInPlane)].reset_index(drop=True)
            planePoints = planePoints[["x", "y", "z", "dist"]]

            notPlanePoints = pointsdf.copy().loc[~pointsdf.index.isin(bestPointsInPlane)]
            notPlanePoints = notPlanePoints[["x", "y", "z"]]

        return bestPlane, planePoints, notPlanePoints

    planes = []
    pointsPlanes = []

    heightGroups = __heightSplit(lasDF) 
    for partialLasDF in heightGroups:
        print(partialLasDF.head())
        currentHeightPlanes = []
        currentHeightPoints = []
        try:
            bestPlane, planePoints, notPlanePoints = __ransac(partialLasDF)
            currentHeightPlanes.append(bestPlane)
            currentHeightPoints.append(planePoints)
        except Exception as e:
            print(e)
        try:
            while (len(notPlanePoints)/len(partialLasDF) > stoppingPercentage):
                bestPlane, planePoints, notPlanePoints = __ransac(notPlanePoints) 
                currentHeightPlanes.append(bestPlane)
                currentHeightPoints.append(planePoints)
        except Exception as e:
            print(e)
        finally:
            planes.append(currentHeightPlanes)
            pointsPlanes.append(currentHeightPoints)
    print(planes)
    return planes, pointsPlanes
"""

def ransacSimple(lasDF, stoppingPercentage = 0.2):
    def __heightSplit(lasDF, heightThreshold = 0.45, filter = True):
        newdf = lasDF.copy().sort_values("z").reset_index(drop=True)
        newdf["deltaZ"] = np.concatenate(([0], newdf.z[1:len(lasDF)].values - newdf.z[0:len(lasDF)-1].values))

        heightGroups = []
        lastSplit = 0

        for i in range(1,len(newdf)):
            if(newdf.deltaZ[i] > heightThreshold):
                heightGroups.append(newdf.iloc[lastSplit:i])
                lastSplit = i

        # Append "final group"
        if(lastSplit != i):
            heightGroups.append(newdf.iloc[lastSplit:i])
            
        # Filter, if wanted
        if(not filter): 
            return heightGroups

        else:
            filteredHeightGroups = heightGroups.copy()
            
            toDelete = []

            # We delete all those with 3 points or less
            for x in range(len(filteredHeightGroups)):
                if(len(filteredHeightGroups[x]) <= 3):
                    toDelete.append(x)

            toDelete.reverse() #Change order so it deletes last groups first (thus indexes are not modified during the process)
            for x in toDelete:
                del filteredHeightGroups[x]

            return filteredHeightGroups

    planes = []
    pointsPlanes = []

    heightGroups = __heightSplit(lasDF) 
    for partialLasDF in heightGroups:
        currentHeightPlanes, currentHeightPoints = guidedRansac(partialLasDF)

        planes.append(currentHeightPlanes)
        pointsPlanes.append(currentHeightPoints)
   
    print(planes)
    return planes, pointsPlanes

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
        for j in range(len(planes[i])):
            a, b, d = planes[i][j][0], planes[i][j][1], planes[i][j][3]
            z_actual = pointsPlanes[i][j].z
            z_predicted = pointsPlanes[i][j].x*a + pointsPlanes[i][j].y*b + d

    rmse = root_mean_squared_error(z_actual, z_predicted)
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
    lasDF['r'] = lazFile.red/65535.0
    lasDF['b'] = lazFile.blue/65535.0
    lasDF['g'] = lazFile.green/65535.0
    lasDF['intensity'] = lazFile.intensity/65535.0

    # Apply the algorithm
    planes, pointsPlanes = ransacSimple(lasDF)

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
    neighborhood = "70_el Besòs i el Maresme"
    parcelsFolder = basePath + "/Results/" + neighborhood + "/Parcels/"
    parcelsList = []
    constructionsList = []
    totalPointsList = []
    totalPlanesList = []
    unidentifiedPointsList = []
    elapsedTimesList = []
    accuraciesList = []

    for parcel in os.listdir(parcelsFolder)[0:1]:
        parcelPath = parcelsFolder + parcel
        for construction in [x for x in os.listdir(parcelPath) if os.path.isdir(parcelPath + "/" + x)][0:1]:
            constructionFolder = parcelPath + "/" + construction + "/"
            # try:
            pointCount, planesCount, unidentifiedCount, timeDiff, score = detect_planes(constructionFolder)
            
            parcelsList.append(parcel)
            constructionsList.append(construction)
            totalPointsList.append(pointCount)
            totalPlanesList.append(planesCount)
            unidentifiedPointsList.append(unidentifiedCount)
            elapsedTimesList.append(timeDiff)
            accuraciesList.append(score)
            # except Exception as e:
            #     print(parcel, construction, e)
    
    summaryDF = pd.DataFrame({
        'parcel': parcelsList,
        'construction': constructionsList,
        'pointsCount': totalPointsList,
        'planeCount': totalPlanesList,
        'unidentifiedPoints': unidentifiedPointsList,
        'time': elapsedTimesList,
        'accuracy': accuraciesList
        })
    
    print(summaryDF.head())
    # detect_planes(buildingsFolder)