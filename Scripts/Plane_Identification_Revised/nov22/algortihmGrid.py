import numpy as np
import pandas as pd 
import matplotlib.pyplot as plt
from planeIdentification import *
from sklearn.cluster import DBSCAN, KMeans, HDBSCAN
import shutil
import os
import time
import itertools
import tqdm

# import warnings
# warnings.filterwarnings("ignore")

def create_output_folder(directory, deleteFolder = False):
    if not(os.path.isdir(directory)):
        os.makedirs(directory)
    else:
        if(deleteFolder):
            shutil.rmtree(directory)
            os.makedirs(directory)

# We define each algorithm

params1 = [{"distance_threshold":[0.5]}, 
            {
                "useDistanceSampling": [True,],
                "inlierThreshold":[0.01, 0.025, 0.05, 0.10, 0.15, 0.3],
                "num_iterations": [5, 10, 20, 50]
            }]

params2 = [{"distance_threshold":[0.5]}, 
            {
                "useDistanceSampling": [True],
                "inlierThreshold":[0.01, 0.025, 0.05, 0.10, 0.15, 0.3, 100],
                "num_iterations": [5, 10, 20, 50]
            }]
params3 = [{"distance_threshold":[0.5]}, 
            {
                "squareSize":[0.5, 1],
                "polar": [True, False],
                # "DBSCANeps": [0.1, 0.25, 0.5, 1, 1.5, 2],
                # "DBSCANminSamples": [4, 8, 12]
            }]
params4 = [{"distance_threshold":[0.5]}, 
            {
                "squareSize":[0.5, 1],
                "polar": [True, False],
                # "DBSCANeps": [0.5, 1, 2],
                # "DBSCANminSamples": [100, 50, 10]
            },
            {   
            },
            # {
            #     "eps": [0.5, 1, 2],
            #     "min_samples": [100, 50, 10]
            # }
            ]

algorithms =[
            # {"name":"planeExtract", 
            #   "alg": [HeightSplit, PlaneExtraction], 
            #   "parameters": [params1[i].keys() for i in range(len(params1))], 
            #   "values": [[params1[i][key] for key in params1[i].keys()]  for i in range(len(params1))]},
            # {"name":"KPlanes", 
            #   "alg": [HeightSplit, PlanesCluster], 
            #   "parameters": [params2[i].keys() for i in range(len(params2))], 
            #   "values": [[params2[i][key] for key in params2[i].keys()]  for i in range(len(params2))]},
              {"name":"GradientHDBSCAN", 
              "alg": [HeightSplit, GradientCluster], 
              "parameters": [params3[i].keys() for i in range(len(params3))], 
              "values": [[params3[i][key] for key in params3[i].keys()]  for i in range(len(params3))]}
            #    {"name":"GradientDoubleHDBSCAN", 
            #   "alg": [HeightSplit, GradientCluster, HDBSCAN], #"alg": [HeightSplit, GradientCluster, DBSCAN] 
            #   "parameters": [params4[i].keys() for i in range(len(params4))], 
            #   "values": [[params4[i][key] for key in params4[i].keys()]  for i in range(len(params4))]}
              ]

### Now we start the algorithms

basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
neighborhood = "Test_70_el Besòs i el Maresme"
parcelsFolder = basePath + "/Results/" + neighborhood + "/Parcels/"

for algo_dict in tqdm.tqdm(algorithms, desc="Iterating through algorithms", leave=True):
    pipeline_classes = algo_dict["alg"]
    all_parameters = algo_dict["parameters"]
    all_values = algo_dict["values"]
    name = algo_dict["name"]

    all_combinations = []
    for params, values in zip(all_parameters, all_values):
        param_combinations = list(itertools.product(*values))
        all_combinations.append((params, param_combinations))
    
    stage_combinations = []
    for combs in itertools.product(*[c[1] for c in all_combinations]):
        stage_combinations.append(combs)

    for stage_combination in tqdm.tqdm(stage_combinations, desc="Doing all combinations", leave=True):
        pipeline_instances = []
        paramNames = []
        for stage_class, params, combination in zip(pipeline_classes, all_parameters, stage_combination):
            param_dict = dict(zip(params, combination))
            pipeline_instances.append(stage_class(**param_dict))
            paramNames.append([name + "_" + str(x) for name, x in zip(params, combination)])
        paramNames = ["_".join(names) for names in paramNames] 
        
        baseOutputFolder = basePath + "/Results/" + neighborhood + "/Testing Plane ID/" + name + "_" + "__".join(paramNames) + "/"
        create_output_folder(baseOutputFolder)
        timeList = []
        parcelsList = []
        constructionsList = []

        for parcel in tqdm.tqdm(os.listdir(parcelsFolder), desc="Looping through parcels", leave=False):                
            parcelSubfolder = parcelsFolder + parcel + "/"
            for construction in tqdm.tqdm([x for x in os.listdir(parcelSubfolder) if os.path.isdir(parcelSubfolder + x)], desc="Identifying each constructions", leave=False):
                constructionFolder = parcelSubfolder + construction

                lasPath = constructionFolder + "/Map files/" + construction + ".laz"
                lasDF = laspy.read(lasPath)

                start_time = time.time()

                pipeline = ClusterPipeline(pipeline_instances)
                pipeline.fit(lasDF.xyz)
                pipeline.getAllPlanes(lasDF.xyz)

                labels = pipeline.final_labels
                lasDF.classification = labels
                end_time = time.time()

                timeList.append(end_time - start_time)
                parcelsList.append(parcel)
                constructionsList.append(construction)

                summaryDF = pd.DataFrame({"parcel": parcelsList, "construction": constructionsList, "cluster_time": timeList})
                summaryDF.to_csv(baseOutputFolder + "Summary.csv", index=False)

                outputFolder = baseOutputFolder + "/" + parcel + "/"
                create_output_folder(outputFolder)
                lasDF.write(outputFolder + "/" + construction+".laz")

                del lasDF

