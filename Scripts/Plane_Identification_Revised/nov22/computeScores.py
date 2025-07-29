import numpy as np
import pandas as pd 
import matplotlib.pyplot as plt
from planeIdentification import *
from sklearn.cluster import DBSCAN, KMeans
from sklearn.linear_model import LinearRegression
from sklearn.metrics import root_mean_squared_error
import shutil
import os
import time
import itertools
from tqdm import tqdm
import laspy
import geopandas as gpd

basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
neighborhood = "Test_70_el Besòs i el Maresme"

baseOutputFolder = basePath + "/Results/" + neighborhood + "/Testing Plane ID_2/"

mask = "planeExtract"
files = os.listdir(baseOutputFolder)
selected_files = [file for file in files if file.startswith(mask)]
selected_files = files

def compute_silhouette(distances, cluster, labels):

    minIndexes = np.argmin(distances, axis=1)
    a = distances.min(axis=1)
    
    outerDistances = []
    
    for i, row in enumerate(distances):
        ignore_index = minIndexes[i]
        masked_row = np.delete(row, ignore_index)
        min_value = np.min(masked_row)
        outerDistances.append(min_value)

    b = np.array(outerDistances)
    diffTerm = b-a
    maxTerm = np.maximum(b, a)
    individual_silhouette = diffTerm/maxTerm

    mask = np.where(labels == cluster)[0]
    inClusterSilhouette = individual_silhouette[mask]
    silhouetteScore = 1/len(inClusterSilhouette)*np.sum(inClusterSilhouette)

    return silhouetteScore

for experiment in tqdm(selected_files, desc = "Testing each algorithm"):
    parcelsFolder = baseOutputFolder + experiment + "/"

    parcelList = []
    constructionList = []
    n_clusterList = []
    inlierList = []
    RMSElist = []
    silhouetteScoreList = []

    for idx, parcel in enumerate([x for x in os.listdir(parcelsFolder) if os.path.isdir(parcelsFolder+x)]):
        parcel_folder = parcelsFolder + parcel + "/"
        for construction in os.listdir(parcel_folder):
            lasDF = laspy.read(parcel_folder + construction + "/Plane Identification/" + construction + ".laz")
            gpkgFile = parcel_folder + construction + "/Plane Identification/" + construction + ".gpkg"
            try:
                planeID_GPKG = gpd.read_file(gpkgFile)
                clusters = planeID_GPKG.cluster.values
            except:
                pass

            points = lasDF.xyz

            x = lasDF.x
            y = lasDF.y
            z = lasDF.z
            classification = lasDF.classification
            mask = (np.isin(classification, clusters)) & (classification != 255) & (classification != -1)

            # x_filtered = x[mask]
            # y_filtered = y[mask]
            # z_filtered = z[mask]
            classification_filtered = classification[mask]
            
            points_filtered = points[mask,:]
            # Get inlier%
            inlierRatio = len(classification_filtered)/len(classification)
            n_clusters = len(clusters)

            if(inlierRatio == 0):
                parcelList.append(parcel)
                constructionList.append(construction)
                n_clusterList.append(n_clusters)
                inlierList.append(inlierRatio)
                RMSElist.append(0)
                silhouetteScoreList.append(0)
            else:
                # Planes
                planes = []
                for idx, plane in planeID_GPKG.iterrows():
                    a, b, c, d = plane.A, plane.B, -1, plane.D
                    planes.append([a, b, c, d])
                
                # Get distances
                distances = np.zeros((points_filtered.shape[0], len(planes)))
                for plane_idx in range(len(planes)):
                    a, b, c, d = planes[plane_idx][0], planes[plane_idx][1], planes[plane_idx][2], planes[plane_idx][3]
                    distances[:, plane_idx] = np.abs(a * points_filtered[:, 0] + b * points_filtered[:, 1] + c * points_filtered[:, 2] + d) / np.sqrt(a**2 + b**2 + c**2)
                    
                # Get RMSE
                inlierDistance = distances.min(axis=1)
                rmse = np.mean(inlierDistance)
                # Get Silhouette score
                minIndexes = np.argmin(distances, axis=1)
                a = distances.min(axis=1)
                
                outerDistances = []
                
                if(len(planes) > 1):
                    for i, row in enumerate(distances):
                        ignore_index = minIndexes[i]
                        masked_row = np.delete(row, ignore_index)
                        min_value = np.min(masked_row)
                        outerDistances.append(min_value)

                    b = np.array(outerDistances)
                    diffTerm = b-a
                    maxTerm = np.maximum(b, a)
                    individual_silhouette = diffTerm/maxTerm
                    silhouetteScore = 1/len(points[mask])*np.sum(individual_silhouette)
                else:
                    silhouetteScore = 1

                # Store results
                parcelList.append(parcel)
                constructionList.append(construction)
                n_clusterList.append(n_clusters)
                inlierList.append(inlierRatio)
                RMSElist.append(rmse)
                silhouetteScoreList.append(silhouetteScore)

                metricsDF = pd.DataFrame({"parcel": parcelList, "construction": constructionList, "n_clusters": n_clusterList, 
                                        "inlierPercenteage": inlierList, "RMSE": RMSElist, "silhouetteScore": silhouetteScoreList})
                metricsDF.to_csv(parcelsFolder + "metrics.csv", index=False)