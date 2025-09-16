import os
from tqdm import tqdm
import geopandas as gpd
import pandas as pd 

def get_silhouettes_DF(resultsPath, experiment):
    try:
        parcelsFolder = resultsPath + experiment + "/"

        parcelList = []
        constructionList = []
        clusterList = []
        areaList = []
        silhouetteList = []

        for parcel in tqdm(os.listdir(parcelsFolder), desc="Clustering: Looping through parcels", leave=False):
            parcelSubfolder = parcelsFolder + parcel + "/"
            for construction in tqdm([x for x in os.listdir(parcelSubfolder) if os.path.isdir(parcelSubfolder + x)],  desc="Clustering: Working on constructions", leave=False):
                constructionFolder = parcelSubfolder + construction + "/"
                resultsFile = constructionFolder + "/Plane Identification/" + construction + ".gpkg"
                resultsGDF = gpd.read_file(resultsFile)

                for idx, row in resultsGDF.iterrows():
                    parcelList.append(parcel)
                    constructionList.append(construction)
                    clusterList.append(row["cluster"])
                    areaList.append(row["geometry"].area)
                    silhouetteList.append(row["silhouette"])

        finalDF = pd.DataFrame({"parcel": parcelList, "construction":constructionList, "cluster":clusterList, "area": areaList, "silhouette":silhouetteList})

        exportPath = resultsPath + experiment + "_Metrics.txt"
        finalDF.to_csv(exportPath, index=None)
        return finalDF
    except:
        print(experiment)

def group_by_constructions(metricsDF):
    result = (metricsDF.groupby(["parcel", "construction"]).apply(lambda g: pd.Series({
        "clusters": list(g["cluster"]), 
        "avg_silhouette": (g["silhouette"] * g["area"]).sum() / g["area"].sum() 
        }
        )).reset_index())
    return result

if __name__ == "__main__":
    resultsPath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Final Version/Results/"
    # experiment = "kPlanes_distance_threshold_0p5_inlierThreshold_0p1_num_iterations_5"

    for experiment in [x for x in os.listdir(resultsPath) if (os.path.isdir(resultsPath+x)) and (x.startswith("v2"))]:
        get_silhouettes_DF(resultsPath, experiment)

    # metricsFilePath = "planeExtract_distance_threshold_0p5_inlierThreshold_0p15_num_iterations_50_Metrics.txt"
    # metricsFile = resultsPath + metricsFilePath 
    # metricsDF = pd.read_csv(metricsFile)
    # group_by_constructions(metricsDF)