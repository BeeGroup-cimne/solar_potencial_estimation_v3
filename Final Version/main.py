import BuildingExtraction
import RequestLiDAR
import WeatherDownload
import SegmentatorLiDAR
import Cluster
import PolygonObtention
import Shading
import PanelPlacement
import SolarSimulation

from utils import create_output_folder, copy_folder
import time

wd = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Final Version/"

parcelsFilePath = wd + "Data/SelectedParcels.gpkg"
constructionsFilePath = wd + "Data/SelectedConstructions.gpkg"
experiment_name = "Experiment 4"
reuseFolder = True
copy_from = "Experiment 1" # This only makes sense if reuseFolder = Ture

clustering_pipeline = Cluster.ClusterPipeline([
    Cluster.HeightSplit(distance_threshold = 0.45),  # First clustering stage
    Cluster.kPlanes(inlierThreshold=0.15, num_iterations=5, maxPlanes=6)
    # Cluster.PlaneExtraction(inlierThreshold=0.3, num_iterations=50)
])

pysam_files = ["/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Scripts/sunEstimation/pysam_template_pvwattsv8.json",
    "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Scripts/sunEstimation/pysam_template_grid.json"]

###############################################################################################################################################################
#### The code below does not need to be modified ####
###############################################################################################################################################################


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
# Cluster.assign_clusters(parcelsFolder, clustering_pipeline)

# stop_time = time.time()
# timeLog.append("Clustering:" + str(stop_time-start_time) + "\n")
# start_time = time.time()

# # Step 7: convert clusters to polygons
# PolygonObtention.generatePolygons(parcelsFolder)

# stop_time = time.time()
# timeLog.append("Polygon_Generation:" + str(stop_time-start_time) + "\n")
# start_time = time.time()

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

# Step 10: simulate energy
tmyfile = TMYFolder + "419806_41.41_2.22_tmy-2022.csv"
SolarSimulation.simulatePySAM(parcelsFolder, tmyfile, pysam_files) # Results are in Wh/m² for genertaed energy and kWh/m² for radiation
SolarSimulation.panelYearly(parcelsFolder)

stop_time = time.time()
timeLog.append("Simulating_Solar:" + str(stop_time-start_time) + "\n")
start_time = time.time()

# Write time results
with open(wd + "Results/" + experiment_name + "_TimeLog.txt", "w") as file:
    for row in timeLog:
        file.write(row)