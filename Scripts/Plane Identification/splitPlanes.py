from sklearn.linear_model import LinearRegression
from sklearn.decomposition import PCA
from tqdm import tqdm
import pandas as pd
import numpy as np
import os
import csv
import shutil
import time


def create_output_folder(directory, deleteFolder = False):
    if not(os.path.isdir(directory)):
        os.makedirs(directory)
    else:
        if(deleteFolder):
            shutil.rmtree(directory)
            os.makedirs(directory)


def splitThePlane(planePoints, threshold = 2):
    df = planePoints.copy()
    df_reduced = PCA(n_components=2).fit_transform(df[["x","y"]])
    df["PCAx"] = df_reduced[:, 0]
    df["PCAy"] = df_reduced[:, 1]
    df = df.sort_values(["PCAx"], ascending=True).reset_index(drop=True)
    df["deltaX"] = [df.PCAx[i] - df.PCAx[i-1] if i>0 else 0 for i in range(len(df))]

    df = df.sort_values(["PCAy"], ascending=True).reset_index(drop=True)
    df["deltaY"] = [df.PCAy[i] - df.PCAy[i-1] if i>0 else 0 for i in range(len(df))]

    dfs = []
    indices = df.index[(df['deltaX'] > threshold) | (df['deltaY'] > threshold)].tolist()
    indices = [0] + indices + [len(df)]

    for i in range(len(indices) - 1):
        dfs.append(df[["x", "y", "z"]].iloc[indices[i]:indices[i+1]].reset_index(drop=True))
    
    return dfs

def split_planes(constructionFolder):
    start = time.time()

    inputFolder = constructionFolder + "/Plane Processing/Plane Merging/"
    outputFolder = constructionFolder + "/Plane Processing/Plane Splitting/"
    create_output_folder(outputFolder + "/Plane Lists/", deleteFolder=True)
    create_output_folder(outputFolder + "/Plane Points/", deleteFolder=True)

    for planeListFile in os.listdir(inputFolder + "/Plane Lists/"):
        heightGroup = planeListFile.replace(".csv", "")
        planeLists = []
        planePoints = []

        for file in [file for file in os.listdir(inputFolder + "/Plane Points/") if file.startswith(heightGroup)]:
            df = pd.read_csv(inputFolder + "/Plane Points/" + file, header=None)
            df = df.rename(columns={0:'x', 1:'y', 2:'z'})
            planePoints.append(df)

            lm = LinearRegression()
            lm.fit(df[["x", "y"]], df.z)
            planeLists.append([lm.coef_[0], lm.coef_[1], -1, lm.intercept_])

        # Come on, do something
        for i in range(len(planePoints)):
            splitted = splitThePlane(planePoints[i])
            planePoints[i] = splitted[0]
            for j in range(1, len(splitted)):
                planePoints.append(splitted[j])
                planeLists.append(planeLists[i])
        
        # Save final plane lists and planePoints
        with open(outputFolder + "/Plane Lists/" + heightGroup + ".csv", "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerows(planeLists)

        for i in range(len(planePoints)):
            filename = outputFolder + "/Plane Points/" + heightGroup + "_" + str(i) + ".csv" #str(i).zfill(2)
            planePoints[i][["x", "y", "z"]].to_csv(filename, header=None, index=False)

    finish = time.time()

    # Metrics
    elapsed_time = finish-start
    return elapsed_time


if __name__ == "__main__":
    basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
    neighborhood = "70_el Besòs i el Maresme"
    parcelsFolder = basePath + "/Results/" + neighborhood + "/Parcels/"

    parcelsList = []
    constructionsList = []
    elapsedTimesList = []
    for parcel in tqdm(os.listdir(parcelsFolder)):
        parcelPath = parcelsFolder + parcel
        for construction in [x for x in os.listdir(parcelPath) if os.path.isdir(parcelPath + "/" + x)]:
            constructionFolder = parcelPath + "/" + construction + "/"
            try:
                elapsed_time = split_planes(constructionFolder)
                elapsedTimesList.append(elapsed_time)
                parcelsList.append(parcel)
                constructionsList.append(construction)

            except Exception as e:
                print(parcel, construction, e)

    summaryDF = pd.DataFrame({
    'parcel': parcelsList,
    'construction': constructionsList,
    'time': elapsedTimesList
    })

    print(summaryDF.head())