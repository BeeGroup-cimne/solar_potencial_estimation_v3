import pandas as pd # Handle dataframes
from sklearn.linear_model import LinearRegression, RANSACRegressor
import numpy as np
from scipy.optimize import minimize
import math

import time

def distances(pointsPlanes, planes):
    totalDist = 0
    totalPlanePoints = 0
    for i in range(len(planes)):
        plane = planes[i]
        A, B, C, D = plane[0], plane[1], plane[2], plane[3]
        planePoints = pointsPlanes[i]
        planePoints["distance"] = abs(A*planePoints.x+ B*planePoints.y + C*planePoints.z + D) / math.sqrt(A**2 + B**2 + C**2)

        totalDist += sum(planePoints.distance)
        totalPlanePoints += len(planePoints)
    
    return totalDist/totalPlanePoints

class TimeoutException(Exception):
    pass

def simpleRansac(lasDF, timeout=30):
    start_time = time.time()

    bestPlanes = []
    bestPlanePoints = []
    bestScore = -np.inf
    n = 1

    if(len(lasDF) <= 3):
        return([], [])
    
    while(True):

        planes = []
        pointsPlanes = []
        scores = []

        remaining_points = lasDF.copy()

        current_time = time.time()

        if current_time - start_time > timeout:
            raise TimeoutException(f"Timeout of {timeout} seconds reached!")

        for i in range(n):
            current_time = time.time()
            if current_time - start_time > timeout:
                raise TimeoutException(f"Timeout of {timeout} seconds reached!")


            if len(remaining_points) > 3:
                X = remaining_points[["x", "y"]].values
                y = remaining_points[["z"]].values
                
                ransac_model = RANSACRegressor(residual_threshold = 0.15)
                ransac_model.fit(X, y)

                plane = ransac_model.estimator_.coef_[0][0], ransac_model.estimator_.coef_[0][1], -1, ransac_model.estimator_.intercept_[0]
                planePoints = remaining_points.copy().loc[ransac_model.inlier_mask_].reset_index(drop=True) 
                remaining_points = remaining_points.copy().loc[np.logical_not(ransac_model.inlier_mask_)].reset_index(drop=True) 

                if(len(planePoints) >= 3):
                    Xinliers = planePoints[["x", "y"]].values
                    Yinliers = planePoints[["z"]].values

                    planes.append(plane)
                    pointsPlanes.append(planePoints)
                    scores.append(ransac_model.estimator_.score(Xinliers, Yinliers))
            else:
                break

        score = -sum(x**2 for x in scores)/n
        # score = sumSTD
        # print(score)
        if(score < bestScore):
            break
        else:
            bestPlanes = planes
            bestPlanePoints = pointsPlanes
            bestScore = score
            n = n+1

    # for plane in planes:
    #     print("\t", plane[0], plane[1], plane[2], plane[3])

    return (planes, pointsPlanes)
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



def ransacGradientBoosted(lasDF, stoppingPercentage = 0.2):
    planes = []
    pointsPlanes = []

    heightGroups = __heightSplit(lasDF) 
    for partialLasDF in heightGroups:
        currentHeightPlanes, currentHeightPoints = simpleRansac(partialLasDF)

        planes.append(currentHeightPlanes)
        pointsPlanes.append(currentHeightPoints)
   
    return planes, pointsPlanes