from shapely import Polygon, MultiPolygon, get_rings, unary_union
import numpy as np
import math
import os
import pandas as pd
from sklearn.linear_model import LinearRegression

def planeAngle(plane1, plane2):
    A1, B1, C1 = plane1[0], plane1[1], plane1[2]
    A2, B2, C2 = plane2[0], plane2[1], plane2[2]
    cosPhi = (A1*A2+B1*B2+C1*C2)/(math.sqrt(A1**2+B1**2+C1**2)*math.sqrt(A2**2+B2**2+C2**2))
    phi = np.arccos(cosPhi)*180/np.pi
    return phi

def planePointDistance(planePoints, plane):
    A, B, C, D = plane[0], plane[1], plane[2], plane[3]
    distance = np.mean(abs(A*planePoints[:,0]+ B*planePoints[:,1] + C*planePoints[:,2] + D) / math.sqrt(A**2 + B**2 + C**2))
    return distance

def fillMatrix(planeLists,  X, labels):
    distanceMatrix = np.empty((len(planeLists), len(planeLists)))
    angleMatrix = np.empty((len(planeLists), len(planeLists)))

    for i in range(len(planeLists)):
        for j in range(len(planeLists)):
            if i == j:
                distanceMatrix[i][j] = 0
                angleMatrix[i][j] = 0
            else:
                distanceMatrix[i][j] = planePointDistance(X[np.where(labels == i), :][0], planeLists[j])
            
            if j < i:
                angle = planeAngle(planeLists[i], planeLists[j])
                angleMatrix[i][j] = angle
                angleMatrix[j][i] = angle
    
    return distanceMatrix, angleMatrix

def canSimplify(distanceMatrix, angleMatrix, distanceThreshold=0.3, angleThreshold=5):
    coordinates = [-1, -1]
    for i in range(len(distanceMatrix)):
        for j in range(len(distanceMatrix)):
            if i != j:
                if(distanceMatrix[i][j] <= distanceThreshold) and (angleMatrix[i][j] <= angleThreshold):
                    return [i,j]
    return coordinates

def deletePositions(labels, planeLists, i, j):
    if i>j:
        planeLists.pop(i) 
        planeLists.pop(j)
    else:
        planeLists.pop(j) 
        planeLists.pop(i)
    
    corrected_labels = labels
    corrected_labels[np.where(corrected_labels == j)] = i

    unique_labels = np.unique(corrected_labels)
    mapping = {label: i for i, label in enumerate(unique_labels) if label != -1}
    corrected_labels = np.array([mapping[label] if label in mapping else -1 for label in labels])

    return corrected_labels, planeLists


def merge_planes(X, labels, planes):

    planeLists = []

    for idx, planeEq in enumerate(planes):
        planeLists.append([planeEq.coef_[0], planeEq.coef_[1], -1, planeEq.intercept_])

    distanceMatrix, angleMatrix = fillMatrix(planeLists, X, labels)
    simplifyPos = canSimplify(distanceMatrix, angleMatrix)

    while(simplifyPos[0] != -1):
        i, j = simplifyPos[0], simplifyPos[1]
        
        toMerge = X[np.where((labels == i) | (labels == j)), :][0]

        lm = LinearRegression()
        lm.fit(toMerge[:,0:2], toMerge[:,2])
        planeLists.append([lm.coef_[0], lm.coef_[1], -1, -lm.intercept_])
        
        # print(len(np.unique(labels)))
        labels, planeLists = deletePositions(labels, planeLists, i, j)
        # print(len(np.unique(labels)))
        distanceMatrix, angleMatrix = fillMatrix(planeLists, X, labels)
        simplifyPos = canSimplify(distanceMatrix, angleMatrix)

    return labels, planeLists


def delete_polygons_by_area(geometry, threshold):
    if isinstance(geometry, Polygon):
        return geometry if geometry.area >= threshold else None
    elif isinstance(geometry, MultiPolygon):
        filtered_polygons = [poly for poly in list(geometry.geoms) if poly.area >= threshold]
        if len(filtered_polygons) == 1:
            return filtered_polygons[0]
        elif len(filtered_polygons) > 1:
            return MultiPolygon(filtered_polygons)
        else:
            return None
    return geometry  # For non-polygon geometries, return as-is

def clean_holes(geometry, threshold): #vorClipped["geometry"] = vorClipped["geometry"].apply(lambda geom: clean_holes(geom, 0.25))
    # Don't know why, but works bad
    if isinstance(geometry, Polygon):
        ext = Polygon(geometry.exterior)      
        for hole in geometry.interiors:
            if(hole.area > threshold): 
                ext = ext.difference(hole)

        return ext
    elif isinstance(geometry, MultiPolygon):
        cleaned_polygons = []
        for geom in list(geometry.geoms):
            ext = Polygon(geom.exterior)
            
            for hole in geom.interiors:
                if(hole.area > threshold): 
                    ext = ext.difference(hole)

            cleaned_polygons.append(ext)
        return MultiPolygon(cleaned_polygons)
    
    return geometry  # For non-polygon geometries, return as-is

# vorClipped["geometry"] = vorClipped["geometry"].apply(lambda geom: filter_polygons_by_area(geom, 5))
# vorClipped = vorClipped[vorClipped.geometry != None] 