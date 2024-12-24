import matplotlib.pyplot as plt
import geopandas as gpd
import laspy
import os
import shutil
import time
from tqdm import tqdm
import numpy as np

from planeIdentification import *
from getVoronoiClipped import getVoronoiClipped
from planeProcessing import *
from sklearn.cluster import DBSCAN, KMeans
from sklearn.linear_model import LinearRegression
from shapely import unary_union, GeometryCollection

def create_output_folder(directory, deleteFolder = False):
    if not(os.path.isdir(directory)):
        os.makedirs(directory)
    else:
        if(deleteFolder):
            shutil.rmtree(directory)
            os.makedirs(directory)

basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
neighborhood = "Test_70_el Besòs i el Maresme"
parcelsFolder = basePath + "/Results/" + neighborhood + "/Parcels/"

def __getTiltAzimuth(normal):
        """
        Given the normal vector of a plane, returns the tilt and azimuth of that plane.
        Tilt goes from 0 (horizontal) to 90 degrees (vertical) whereas azimuth goes from 0 (pointing north) to 360 degrees, growing clockwise

        #### Inputs:
        - normal: 3 element array (x,y,z from the normal vector, i.e, a,b,c parameters of the plane equation)
        
        #### Outputs:
        -  tilt, azimuth: in degreees
        """

        # Check if z is negative, plane normal must be pointing upwards
        normal = np.array(normal)
        if(normal[2] < 0):
            normal = -normal
        
        # Azimuth
        alpha = math.degrees(math.atan2(normal[1], normal[0]))
        azimuth = 90 - alpha
        if azimuth >= 360.0:
            azimuth -= 360.0
        elif azimuth < 0.0:
            azimuth += 360.0
        
        # Tilt
        t = math.sqrt(normal[0] ** 2 + normal[1] ** 2)
        if t == 0:
            tilt = 0.0
        else:
            tilt = 90 - math.degrees(math.atan(normal[2] / t)) # 0 for flat roof, 90 for wall/vertical roof
        tilt = round(tilt, 3)

        return (tilt, azimuth)


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

basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
neighborhood = "Test_70_el Besòs i el Maresme"
parcelsFolder = basePath + "/Results/" + neighborhood + "/Parcels/"
baseOutputFolder = basePath + "/Results/" + neighborhood + "/Testing Plane ID_2/"


mask = "GradientHDBSCAN_distance_threshold"
files = os.listdir(baseOutputFolder)
selected_files = [file for file in files if file.startswith(mask)]

for algorithm in tqdm(selected_files, desc = "Testing each algorithm"):
    experimentFolder = baseOutputFolder + algorithm + "/"
    for parcel in tqdm([x for x in os.listdir(experimentFolder) if os.path.isdir(experimentFolder + x)], desc="Looping through parcels", leave=False):
        parcelSubfolder = experimentFolder + parcel + "/"
        for construction in tqdm([x for x in os.listdir(parcelSubfolder) if os.path.isdir(parcelSubfolder + x)],  desc="Working on constructions", leave=False):
            constructionFolder = parcelSubfolder + construction
            resultsFolder = constructionFolder + "/Plane Identification/"
            lasPath = resultsFolder + construction + ".laz"
            lasDF = laspy.read(lasPath)
            
            gpkgFile = parcelsFolder + parcel + "/" + construction + "/Map files/" + construction + ".gpkg"
            cadasterGDF = gpd.read_file(gpkgFile)

            labels = lasDF.classification
            vorClipped = getVoronoiClipped(lasDF.xyz, labels, cadasterGDF)
            vorClipped = vorClipped[vorClipped.cluster != 255]  
            
            #Z = Ax+By+D
            A_list = []
            B_list = []
            D_list = []
            tilt_list = []
            azimuth_list = []
            for idx in vorClipped.cluster:
                points = lasDF.xyz[np.where(lasDF.classification == idx)]
                planeParams = LinearRegression().fit(points[:, 0:2], points[:, 2])
                A_list.append(planeParams.coef_[0])
                B_list.append(planeParams.coef_[1])
                D_list.append(planeParams.intercept_)
                tilt,azimuth = __getTiltAzimuth([planeParams.coef_[0], planeParams.coef_[1], -1, planeParams.intercept_])
                tilt_list.append(tilt)
                azimuth_list.append(azimuth)
            
            silhouette_list = []
            points = lasDF.xyz
            distances = np.zeros((points.shape[0], len(vorClipped.cluster)))

            for plane_idx in range(len(vorClipped.cluster)):
                a, b, c, d = A_list[plane_idx], B_list[plane_idx], -1, D_list[plane_idx]
                distances[:, plane_idx] = np.abs(a * points[:, 0] + b * points[:, 1] + c * points[:, 2] + d) / np.sqrt(a**2 + b**2 + c**2)

            if(len(vorClipped.cluster.values) == 1):
                silhouette_list.append(1)
            else:
                for cluster in vorClipped.cluster.values:
                    silhouette_list.append(compute_silhouette(distances, cluster, labels))
                
            vorClipped["A"] = A_list
            vorClipped["B"] = B_list                                                                                                                                                                                
            vorClipped["D"] = D_list
            vorClipped["tilt"] = tilt_list
            vorClipped["azimuth"] = azimuth_list
            vorClipped["silhouette"] = silhouette_list
            
            vorClipped["geometry"] = vorClipped["geometry"].apply(lambda geom: delete_polygons_by_area(geom, 1))
            vorClipped["geometry"] = vorClipped["geometry"].apply(lambda geom: clean_holes(geom, 0.25))
            

            vorClipped = gpd.clip(vorClipped, cadasterGDF)
            vorClipped = vorClipped[~vorClipped["geometry"].apply(lambda geom: isinstance(geom, GeometryCollection))]
            vorClipped = vorClipped.reset_index(drop=True)

            try:
                for i in reversed(range(len(vorClipped)-1)): 
                    subsequent_geometries = unary_union(vorClipped.iloc[i+1:].geometry)
                    if(vorClipped.geometry[i] != None):
                        vorClipped.at[i, 'geometry'] = vorClipped.geometry.iloc[i].difference(subsequent_geometries)
            except: 
                print("")
                print("Error", algorithm, parcel, construction)
                print("")

            try:
                vorClipped = vorClipped[vorClipped.geometry != None]             
                vorClipped.to_file(constructionFolder + "/Plane Identification/"+construction+".gpkg", driver="GPKG")      
            except:
                print("")
                print(algorithm, parcel, construction)
                print("")