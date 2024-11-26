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

for parcel in tqdm(os.listdir(parcelsFolder)[5:6], desc="Looping through parcels"):
    print(parcel)
    parcelSubfolder = parcelsFolder + parcel + "/"
    for construction in tqdm([x for x in os.listdir(parcelSubfolder)[0:1] if os.path.isdir(parcelSubfolder + x)],  desc="Working on constructions", leave=False):
        constructionFolder = parcelSubfolder + construction
        create_output_folder(constructionFolder + "/Plane Identification/", deleteFolder=True)
        create_output_folder(constructionFolder + "/Plane Identification/Plane Points")

        lasPath = constructionFolder + "/Map files/" + construction + ".laz"
        lasDF = laspy.read(lasPath)
        gpkgFile = constructionFolder + "/Map files/" + construction + ".gpkg"
        cadasterGDF = gpd.read_file(gpkgFile)

        pipeline = ClusterPipeline([
            heightSplit(distance_threshold = 0.45),  # First clustering stage
            # PlanesCluster(inlierThreshold=0.15, minPlanes=5, maxPlanes=7),
            # KMeans(n_clusters=3),
            # DBSCAN(eps=1.5, min_samples=8),
        ])

        pipeline.fit(lasDF.xyz)
        pipeline.getAllPlanes(lasDF.xyz)

        labels = pipeline.final_labels

        lasDF.add_extra_dim(laspy.ExtraBytesParams(
            name="Labels",
            type=np.int64))
        lasDF["Labels"] = labels
        
        lasDF.write(constructionFolder + "/Plane Identification/"+construction+".laz")
        # PlaneProcessing
        # labels, planeLists = merge_planes(lasDF.xyz, labels, pipeline.planes)
       
        vorClipped = getVoronoiClipped(lasDF.xyz, labels, cadasterGDF)
        # vorClipped = vorClipped[vorClipped.cluster != -1]

        #Ax+By+Z=D, but D in planeLists is negative, so we need to multiply by -1
        A_list = []
        B_list = []
        D_list = []

        for idx, planeParams in enumerate(pipeline.planes):
            A_list.append(planeParams.coef_[0])
            B_list.append(planeParams.coef_[1])
            D_list.append(planeParams.intercept_)
        
        # vorClipped["A"] = A_list
        # vorClipped["B"] = B_list                                                                                                                                                                                
        # vorClipped["D"] = D_list

        # vorClipped["geometry"] = vorClipped["geometry"].apply(lambda geom: delete_polygons_by_area(geom, 2))
        # vorClipped = vorClipped[vorClipped.geometry != None] 

        vorClipped.to_file(constructionFolder + "/Plane Identification/"+construction+".gpkg", driver="GPKG")