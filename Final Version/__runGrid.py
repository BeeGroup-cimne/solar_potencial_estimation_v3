import BuildingExtraction
import RequestLiDAR
import WeatherDownload
import SegmentatorLiDAR
import Cluster
import PolygonObtention
import Shading
import PanelPlacement
import SolarSimulation
import AlgorithmGrid
from utils import create_output_folder, copy_folder


import time
import itertools
import numpy as np
from tqdm import tqdm

wd = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Final Version/"

parcelsFilePath = wd + "Data/SelectedParcels.gpkg"
constructionsFilePath = wd + "Data/SelectedConstructions.gpkg"
pysam_files = [wd + "pysam_template_pvwattsv8.json", wd + "pysam_template_grid.json"]

reuseFolder = True
copy_from = "0_Results_for_paper_planeExtract_0p1_Shaded_30cmMeshBuffer100" # This only makes sense if reuseFolder = True


params_list = [
    {"distance_threshold":[0.5]},
    {
        "inlierThreshold":[0.01, 0.05, 0.10, 0.15, 0.3], #, np.inf
        "num_iterations": [5, 10, 20, 50]
    }
]

algorithmDict = {
    "base_name": "v2_planeExtract",
    "algs": [Cluster.HeightSplit, Cluster.PlaneExtraction],
    "parameters": [params_list[i].keys() for i in range(len(params_list))], 
    "values": [[params_list[i][key] for key in params_list[i].keys()]  for i in range(len(params_list))]
}


###############################################################################################################################################################
#### The code below does not need to be modified ####
###############################################################################################################################################################

experiment_names, pipelines = AlgorithmGrid.getPipelines(params_list, algorithmDict) 

for i in tqdm(range(len(experiment_names)), desc = "Algorithms"):

    experiment_name = experiment_names[i]
    clustering_pipeline = pipelines[i]

    resultsFolder = wd + "Results/" + experiment_name + "/"

    timeLog = []

    start_time = time.time()
    TMYFolder = wd + "Data/TMY/"

    if(reuseFolder):
        # Optional steps 12345: copy from another directoy (for multiple experiments)
        originalFolder = wd + "Results/" + copy_from + "/"
        outputFolder = wd + "Results/" + experiment_name + "/"
        copy_folder(originalFolder, outputFolder)
        parcelsFolder = outputFolder
    else:
        parcelsFolder = resultsFolder
        create_output_folder(parcelsFolder)
        # Step 1: extract parcels and building
        BuildingExtraction.extract_parcels(parcelsFilePath, resultsFolder)
        BuildingExtraction.extract_constructions(constructionsFilePath, resultsFolder) # The filter msak may be upgraded

        stop_time = time.time()
        timeLog.append("Extrating_Parcels_Buildings:" + str(stop_time-start_time) + "\n")
        start_time = time.time()

        # Step 2: request LiDAR data
        lidarFolder = wd + "Data/LiDAR/"
        RequestLiDAR.download_LiDAR(lidarFolder, parcelsFolder, buffer=50)

        stop_time = time.time()
        timeLog.append("LiDAR_Downloading:" + str(stop_time-start_time) + "\n")
        start_time = time.time()

        # Step 3: download TMY data
        WeatherDownload.downloadTMY(parcelsFilePath, TMYFolder)

        stop_time = time.time()
        timeLog.append("TMY_Downloading:" + str(stop_time-start_time) + "\n")
        start_time = time.time()

        # Step 4, 5: clip LiDAR building and neighborhood
        lidarFolder = lidarFolder
        SegmentatorLiDAR.building_clip(lidarFolder, parcelsFolder) # This could be optimized if buffered and nonbuffered laz were simultaneously generated
        stop_time = time.time()
        timeLog.append("Clipping_LiDAR_Constructions:" + str(stop_time-start_time) + "\n")
        start_time = time.time()

        SegmentatorLiDAR.building_clip(lidarFolder, parcelsFolder, buffer=50, filterConstructions=False)
        stop_time = time.time()
        timeLog.append("Clipping_LiDAR_Neighborhood:" + str(stop_time-start_time) + "\n")
        start_time = time.time()

    # Step 6: cluster
    Cluster.assign_clusters(parcelsFolder, clustering_pipeline)

    stop_time = time.time()
    timeLog.append("Clustering:" + str(stop_time-start_time) + "\n")
    start_time = time.time()

    # Step 7: convert clusters to polygons
    PolygonObtention.generatePolygons(parcelsFolder)

    stop_time = time.time()
    timeLog.append("Polygon_Generation:" + str(stop_time-start_time) + "\n")
    start_time = time.time()

    # # Step 8: compute shading
    # Shading.computeShading(parcelsFolder)

    # stop_time = time.time()
    # timeLog.append("Shading:" + str(stop_time-start_time) + "\n")
    # start_time = time.time()

    # # Step 9: place panels
    # PanelPlacement.placePanels(parcelsFolder)

    # stop_time = time.time()
    # timeLog.append("Placing_Panels:" + str(stop_time-start_time) + "\n")
    # start_time = time.time()

    # # Step 10: simulate energy
    # tmyfile = TMYFolder + "419806_41.41_2.22_tmy-2022.csv"
    # SolarSimulation.simulatePySAM(parcelsFolder, tmyfile, pysam_files) # Results are in Wh/m² for genertaed energy and kWh/m² for radiation
    # SolarSimulation.panelYearly(parcelsFolder)

    # stop_time = time.time()
    # timeLog.append("Simulating_Solar:" + str(stop_time-start_time) + "\n")
    # start_time = time.time()

    # Write time results
    with open(wd + "Results/" + experiment_name + "_TimeLog.txt", "w") as file:
        for row in timeLog:
            file.write(row)