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

buffer=50
parcelsFilePath = wd + "Data/SelectedParcels.gpkg"
constructionsFilePath = wd + "Data/SelectedConstructions.gpkg"
pysam_files = [wd + "pysam_template_pvwattsv8.json", wd + "pysam_template_grid.json"]

reuseFolder = False
copy_from = "0_Results_for_paper_planeExtract_0p1_Shaded_30cmMesh" # This only makes sense if reuseFolder = True
experiment_name = "Best_Identifications_v2_planeExtract"
clustering_pipeline = Cluster.ClusterPipeline([
    Cluster.HeightSplit(distance_threshold = 0.5),  # First clustering stage
    # Cluster.kPlanes(inlierThreshold=0.15, num_iterations=5, maxPlanes=6)
    Cluster.PlaneExtraction(inlierThreshold=0.1, num_iterations=50)
])


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
    # create_output_folder(parcelsFolder)
    # # Step 1: extract parcels and building
    # BuildingExtraction.extract_parcels(parcelsFilePath, resultsFolder)
    # BuildingExtraction.extract_constructions(constructionsFilePath, resultsFolder) # The filter msak may be upgraded

    # stop_time = time.time()
    # timeLog.append("Extrating_Parcels_Buildings:" + str(stop_time-start_time) + "\n")
    # start_time = time.time()

    # # Step 2: request LiDAR data
    lidarFolder = wd + "Data/LiDAR/"
    # RequestLiDAR.download_LiDAR(lidarFolder, parcelsFolder, buffer=buffer)

    # stop_time = time.time()
    # timeLog.append("LiDAR_Downloading:" + str(stop_time-start_time) + "\n")
    # start_time = time.time()

    # # Step 3: download TMY data
    # tmyFile = WeatherDownload.downloadTMY(parcelsFilePath, TMYFolder)

    # stop_time = time.time()
    # timeLog.append("TMY_Downloading:" + str(stop_time-start_time) + "\n")
    # start_time = time.time()

    # # Step 4, 5: clip LiDAR building and neighborhood
    # SegmentatorLiDAR.building_clip(lidarFolder, parcelsFolder) # This could be optimized if buffered and nonbuffered laz were simultaneously generated
    # stop_time = time.time()
    # timeLog.append("Clipping_LiDAR_Constructions:" + str(stop_time-start_time) + "\n")
    # start_time = time.time()

    # SegmentatorLiDAR.building_clip(lidarFolder, parcelsFolder, buffer=buffer, filterConstructions=False)
    # stop_time = time.time()
    # timeLog.append("Clipping_LiDAR_Neighborhood:" + str(stop_time-start_time) + "\n")
    # start_time = time.time()

# # Step 6: cluster
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
# Shading.computeShading(parcelsFolder, buffer)

# stop_time = time.time()
# timeLog.append("Shading:" + str(stop_time-start_time) + "\n")
# start_time = time.time()

# Step 9: place panels
PanelPlacement.placePanels(parcelsFolder)

stop_time = time.time()
timeLog.append("Placing_Panels:" + str(stop_time-start_time) + "\n")
start_time = time.time()

# Step 10: simulate energy
tmyFile = WeatherDownload.downloadTMY(parcelsFilePath, TMYFolder)
tmyfilePath = TMYFolder + tmyFile
SolarSimulation.panelSimulate(parcelsFolder, tmyfilePath, pysam_files) # Results are in kWh/panel for everything
# SolarSimulation.simulatePySAM_Grid(parcelsFolder, tmyfile, pysam_files) # Longer, as it solves all sampled points. Results are in kWh/m² for  both generated energy and radiation
# SolarSimulation.panelYearly(parcelsFolder) 

# stop_time = time.time()
# timeLog.append("Simulating_Solar:" + str(stop_time-start_time) + "\n")
# start_time = time.time()

# # Write time results
# with open(wd + "Results/" + experiment_name + "_TimeLog.txt", "w") as file:
#     for row in timeLog:
#         file.write(row)