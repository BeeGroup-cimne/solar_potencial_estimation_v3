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
neighborhood = "7_P.I. Can Petit"
# neighborhood = "70_el Besòs i el Maresme"
parcelsFolder = basePath + "/Results/" + neighborhood + "/Parcels/"

for parcel in tqdm(os.listdir(parcelsFolder)[3:], desc="Looping through parcels"):

    # print(parcel)
    parcelSubfolder = parcelsFolder + parcel + "/"
    for construction in tqdm([x for x in os.listdir(parcelSubfolder) if os.path.isdir(parcelSubfolder + x)],  desc="Working on constructions", leave=False):
        # print(construction)
        constructionFolder = parcelSubfolder + construction
        create_output_folder(constructionFolder + "/Plane Identification/", deleteFolder=True)

        lasPath = constructionFolder + "/Map files/" + construction + ".laz"
        lasDF = laspy.read(lasPath)
        gpkgFile = constructionFolder + "/Map files/" + construction + ".gpkg"
        cadasterGDF = gpd.read_file(gpkgFile)
        try:
            pipeline = ClusterPipeline([
                HeightSplit(distance_threshold = 0.45),  # First clustering stage
                PlaneExtraction(inlierThreshold=0.3, num_iterations=200),
            ])
            pipeline.fit(lasDF.xyz)

        except:
            print(" ", parcel, construction, " ")

        lasDF.classification  = pipeline.final_labels

        lasDF.write(constructionFolder + "/Plane Identification/"+construction+".laz")
    