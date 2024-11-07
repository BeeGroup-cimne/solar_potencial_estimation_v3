import requests
from tqdm import tqdm
import os
import shutil

# https://datacloud.icgc.cat/datacloud/lidar-territorial/laz_unzip/full10km2650/lidar-territorial-v3r0-full1km265509-2021-2023.laz

base_url = "https://datacloud.icgc.cat/datacloud/lidar-territorial/laz_unzip/" 

def create_output_folder(directory, deleteFolder = False):
    if not(os.path.isdir(directory)):
        os.makedirs(directory)
    else:
        if(deleteFolder):
            shutil.rmtree(directory)
            os.makedirs(directory)

def download_LIDAR_CAT(squares, outputFolder):
    create_output_folder(outputFolder)
    
    for square in tqdm(squares):
        mainZone = int(str(square)[0:2] + str(square)[3:5])
        url = base_url + f"full10km{mainZone}/" + f"lidar-territorial-v3r0-full1km{square}-2021-2023.laz"
        filename = outputFolder + f"{square}.laz"

        response = requests.get(url, stream=True)
        with open(filename, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192): 
                file.write(chunk)

if __name__ == "__main__":
    squares = [433586, 434586, 435586, 433585, 434585, 435585, 433584, 434584, 435584, 433583, 434583, 435583]
    basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
    outputFolder = "RAW_Data/LiDAR/"
    download_LIDAR_CAT(squares, basePath + outputFolder)