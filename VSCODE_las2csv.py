import pandas as pd
import laspy

import os
import shutil

def create_output_folder(directory, deleteFolder = False):
    if not(os.path.isdir(directory)):
        os.makedirs(directory)
    else:
        if(deleteFolder):
            shutil.rmtree(directory)
            os.makedirs(directory)


def las2csv(lasPath, outputPath):
    lasfile = laspy.read(lasPath)
    lasDF = pd.DataFrame(lasfile.xyz)
    lasDF = lasDF.rename(columns={0:"x", 1:"y", 2:"z"})
    lasDF.to_csv(outputPath, index=False)
    print("Done!")

if __name__ == "__main__":
    basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
    # # Already done
    # lasPath = basePath + "Data/Merged_LiDAR.laz"
    # outputPath = basePath + "Data/Merged_LiDAR.csv"
    # las2csv(lasPath, outputPath)

    filesToExport = [433584, 433585, 433586, 434584, 434585, 434586, 435584, 435585, 435586]
    create_output_folder(basePath + "Data/LiDAR")
    for file in filesToExport:
        lasPath = basePath + "RAW_Data/LiDAR/" + str(file) + ".laz"
        outputPath = basePath + "Data/LiDAR/" + str(file) + ".csv"
        las2csv(lasPath, outputPath)

