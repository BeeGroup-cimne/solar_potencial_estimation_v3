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
import tqdm
import laspy


basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
neighborhood = "Test_70_el Besòs i el Maresme"

params1 = [{"distance_threshold":[0.5]}, 
            {
                "useDistanceSampling": [True, False],
                "inlierThreshold":[0.01, 0.025, 0.05, 0.10, 0.15, 0.3, 100],
                "num_iterations": [5, 10, 20, 50]
            }]

# params2 = [{"distance_threshold":[0.5]}, 
#             {
#                 "useDistanceSampling": [True, False],
#                 "inlierThreshold":[0.01, 0.025, 0.05, 0.10, 0.15, 0.3, 100],
#                 "num_iterations": [5, 10, 20, 50]
#             }]
# params3 = [{"distance_threshold":[0.5]}, 
#             {
#                 "squareSize":[0.25, 0.5, 1, 2],
#                 "polar": [True, False],
#                 "DBSCANeps": [0.1, 0.25, 0.5, 1, 1.5, 2],
#                 "DBSCANminSamples": [4, 8, 12]
#             }]
# params4 = [{"distance_threshold":[0.5]}, 
#             {
#                 "squareSize":[0.25, 0.5, 1, 2],
#                 "polar": [True, False],
#                 "DBSCANeps": [0.1, 0.25, 0.5, 1, 1.5, 2],
#                 "DBSCANminSamples": [4, 8, 12]
#             },
#             {
#                 "eps": [0.1, 0.25, 0.5, 1, 1.5, 2],
#                 "min_samples": [4, 8, 12]
#             }]

algorithms =[
            {"name":"planeExtract", 
              "alg": [HeightSplit, PlaneExtraction], 
              "parameters": [params1[i].keys() for i in range(len(params1))], 
              "values": [[params1[i][key] for key in params1[i].keys()]  for i in range(len(params1))]},
            # {"name":"KPlanes", 
            #   "alg": [HeightSplit, PlanesCluster], 
            #   "parameters": [params2[i].keys() for i in range(len(params2))], 
            #   "values": [[params2[i][key] for key in params2[i].keys()]  for i in range(len(params2))]},
            #   {"name":"GradientDBSCAN", 
            #   "alg": [HeightSplit, GradientCluster], 
            #   "parameters": [params3[i].keys() for i in range(len(params3))], 
            #   "values": [[params3[i][key] for key in params3[i].keys()]  for i in range(len(params3))]}
            #    {"name":"GradientDoubleDBSCAN", 
            #   "alg": [HeightSplit, GradientCluster, DBSCAN], 
            #   "parameters": [params4[i].keys() for i in range(len(params4))], 
            #   "values": [[params4[i][key] for key in params4[i].keys()]  for i in range(len(params4))]}
              ]

# for algo_dict in tqdm.tqdm(algorithms, desc="Iterating through algorithms", leave=True):
#     pipeline_classes = algo_dict["alg"]
#     all_parameters = algo_dict["parameters"]
#     all_values = algo_dict["values"]
#     name = algo_dict["name"]

#     all_combinations = []
#     for params, values in zip(all_parameters, all_values):
#         param_combinations = list(itertools.product(*values))
#         all_combinations.append((params, param_combinations))
    
#     stage_combinations = []
#     for combs in itertools.product(*[c[1] for c in all_combinations]):
#         stage_combinations.append(combs)

#     for stage_combination in tqdm.tqdm(stage_combinations, desc="Doing all combinations", leave=True):
#         pipeline_instances = []
#         paramNames = []
#         for stage_class, params, combination in zip(pipeline_classes, all_parameters, stage_combination):
#             param_dict = dict(zip(params, combination))
#             pipeline_instances.append(stage_class(**param_dict))
#             paramNames.append([name + "_" + str(x) for name, x in zip(params, combination)])
#         paramNames = ["_".join(names) for names in paramNames] 

baseOutputFolder = basePath + "/Results/" + neighborhood + "/Testing Plane ID/"

for experiment in tqdm.tqdm(os.listdir(baseOutputFolder)):
    parcelsFolder = baseOutputFolder + experiment + "/"

    parcelList = []
    constructionList = []
    n_clusterList = []
    inlierList = []
    RMSElist = []
    silhouetteScoreList = []

    for parcel in tqdm.tqdm([x for x in os.listdir(parcelsFolder) if os.path.isdir(parcelsFolder+x)], desc="Looping through parcels", leave=False):                
        parcelSubfolder = parcelsFolder + parcel + "/"
        for construction in tqdm.tqdm(os.listdir(parcelSubfolder), desc="Identifying each constructions", leave=False):
            lasDF = laspy.read(parcelSubfolder+construction)
            points = lasDF.xyz

            labels = lasDF.classification
            labels = labels.astype(int)
            labels[np.where(labels == 255)] = -1

            # Get inlier%
            inlierRatio = len(labels[labels != -1])/len(labels)
            n_clusters = len(np.unique(labels))

            if(inlierRatio == 0):
                parcelList.append(parcel)
                constructionList.append(construction)
                n_clusterList.append(n_clusters)
                inlierList.append(inlierRatio)
                RMSElist.append(0)
                silhouetteScoreList.append(0)
            else:
                # Get planes
                planes = []
                for i in np.unique(labels[labels != -1]):
                    planePoints = points[np.where(labels == i), :][0]
                    planes.append(LinearRegression().fit(planePoints[:,0:2], planePoints[:,2]))

                distances = np.zeros((points.shape[0], len(planes)))
                for plane_idx in range(len(planes)):
                    distances[:, plane_idx] = abs(points[:,2] - planes[plane_idx].predict(points[:,0:2]))

                # Get RMSE
                inlierDistance = distances.min(axis=1)
                inlierDistance = inlierDistance[np.where(labels != -1)]
                rmse = root_mean_squared_error(np.zeros(len(inlierDistance)), inlierDistance)

                # Get Silhouette score
                if(len(np.unique(labels[labels != -1])) == 1):
                    silhouetteScore = 0
                else:
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
                    silhouetteScore = 1/len(points)*np.sum(individual_silhouette)


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