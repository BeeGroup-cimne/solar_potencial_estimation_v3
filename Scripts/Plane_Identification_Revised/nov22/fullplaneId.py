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

for parcel in tqdm(os.listdir(parcelsFolder), desc="Looping through parcels"):
    # print(parcel)
    parcelSubfolder = parcelsFolder + parcel + "/"
    for construction in tqdm([x for x in os.listdir(parcelSubfolder) if os.path.isdir(parcelSubfolder + x)],  desc="Working on constructions", leave=False):
        constructionFolder = parcelSubfolder + construction
        create_output_folder(constructionFolder + "/Plane Identification/", deleteFolder=True)
        create_output_folder(constructionFolder + "/Plane Identification/Plane Points")

        lasPath = constructionFolder + "/Map files/" + construction + ".laz"
        lasDF = laspy.read(lasPath)
        gpkgFile = constructionFolder + "/Map files/" + construction + ".gpkg"
        cadasterGDF = gpd.read_file(gpkgFile)

        pipeline = ClusterPipeline([
            HeightSplit(distance_threshold = 0.45),  # First clustering stage
            PlanesCluster(inlierThreshold=0.15, num_iterations=20),
            # KMeans(n_clusters=3),
            # DBSCAN(eps=1.5, min_samples=8),
        ])

        pipeline.fit(lasDF.xyz)
        pipeline.getAllPlanes(lasDF.xyz)

        labels = pipeline.final_labels

        # lasDF.add_extra_dim(laspy.ExtraBytesParams(
        #     name="Labels",
        #     type=np.int64))
        
        # PlaneProcessing
        labels, planeLists = merge_planes(lasDF.xyz, labels, pipeline.planes)
        lasDF.classification = labels
        lasDF.write(constructionFolder + "/Plane Identification/"+construction+".laz")

        # plt.scatter(lasDF.x, lasDF.y, c=labels)
        # plt.show()

        # vorClipped = getVoronoiClipped(lasDF.xyz, labels, cadasterGDF)

        
        # #Z = Ax+By+D, but D in planeLists is negative, so we need to multiply by -1
        # A_list = []
        # B_list = []
        # D_list = []

        # for idx, planeParams in enumerate(pipeline.planes):
        #     if idx in vorClipped.cluster:
        #         A_list.append(planeParams.coef_[0])
        #         B_list.append(planeParams.coef_[1])
        #         D_list.append(planeParams.intercept_)
        # # for idx, planeParams in enumerate(planeLists):
        # #     if idx in vorClipped.cluster:
        # #         A_list.append(planeParams[0])
        # #         B_list.append(planeParams[1])
        # #         D_list.append(planeParams[3])

        
        # vorClipped["A"] = A_list
        # vorClipped["B"] = B_list                                                                                                                                                                                
        # vorClipped["D"] = D_list

        # vorClipped = vorClipped[vorClipped.cluster != -1]
        # vorClipped["geometry"] = vorClipped["geometry"].buffer(0.25)
        # vorClipped["geometry"] = vorClipped["geometry"].buffer(-0.25)
        # vorClipped["geometry"] = vorClipped["geometry"].apply(lambda geom: delete_polygons_by_area(geom, 2))
        # vorClipped = vorClipped[vorClipped.geometry != None] 
        
        # vorClipped.to_file(constructionFolder + "/Plane Identification/"+construction+".gpkg", driver="GPKG")

        # vorClipped.plot(edgecolor='black', column="cluster", alpha=0.5, legend=True)
        # plt.show()
        