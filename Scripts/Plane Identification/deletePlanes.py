from functions.folderManagement import create_output_folder

from sklearn.linear_model import LinearRegression
from scipy.spatial import ConvexHull
from shapely import Polygon

from tqdm import tqdm
import pandas as pd
import numpy as np
import os
import math
import csv

def isPlaneTooSmall(pointsInPlane, threshold=2):
    x = pointsInPlane.x
    y = pointsInPlane.y
    
    p = []
    for j in range(len(x)):
        p.append((x[j], y[j]))

    p = np.array(p)
    hull = ConvexHull(p)
    outline = p[hull.vertices,:]

    polygon = Polygon(outline)
    area = polygon.area

    if(area < threshold):
        return True
    return False


def tooFewPoints(pointsInPlane, threshold=3):
    if(len(pointsInPlane) <= threshold):
        return True
    return False

def delete_planes(buildingsFolder, inputSubfolder, outputSubfolder):
    failedBuildings = []
    for buildingDirectory in tqdm(os.listdir(buildingsFolder)):
        try:
            inputFolder = buildingsFolder + buildingDirectory + inputSubfolder
            outputFolder = buildingsFolder + buildingDirectory + outputSubfolder
            create_output_folder(outputFolder + "/Plane Points", deleteFolder=True)

            planeLists = []
            planePoints = []

            for file in os.listdir(inputFolder + "/Plane Points"):
                fileName = inputFolder + "/Plane Points/" + file
                if os.stat(fileName).st_size > 0:
                    df = pd.read_csv(fileName, header=None)
                    df = df.rename(columns={0:'x', 1:'y', 2:'z'})
                    planePoints.append(df)

                lm = LinearRegression()
                lm.fit(df[["x", "y"]], df.z)
                planeLists.append([lm.coef_[0], lm.coef_[1], -1, lm.intercept_])

            # Come on, do something
            toDelete = []
            for i in range(len(planePoints)):
                if(tooFewPoints(planePoints[i])):
                    toDelete.append(i)
                elif(isPlaneTooSmall(planePoints[i])):
                    toDelete.append(i)
                
            toDelete.sort(reverse = True)
            for i in toDelete:
                planePoints.pop(i)
                planeLists.pop(i)

            # Save final plane lists and planePoints
            with open(outputFolder + "/Plane List.csv", "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerows(planeLists)

            for i in range(len(planePoints)):
                filename = outputFolder + "/Plane Points/" + str(i).zfill(2) + ".csv"
                planePoints[i][["x", "y", "z"]].to_csv(filename, header=None, index=False)
        except:
            failedBuildings.append(buildingDirectory)
            # print(buildingDirectory, "FAILED")
    print(failedBuildings, "FAILED")
    
if __name__ == "__main__":
    buildingsFolder = "/home/jaumeasensio/Documents/Projectes/BEEGroup/Solar Estimation v3 - Terrassa/Results/7_P.I. Can Petit/Buildings Results/"
    inputSubfolder = "/2 - Plane Processing/2 - Plane Splitting/"
    outputSubfolder = "/2 - Plane Processing/3 - Plane Deleting/"
    delete_planes(buildingsFolder, inputSubfolder, outputSubfolder)