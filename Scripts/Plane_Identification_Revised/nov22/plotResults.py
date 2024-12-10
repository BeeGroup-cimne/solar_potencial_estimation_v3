import os
import laspy
import numpy as np
import matplotlib.pyplot as plt
import tqdm

base_path = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Results/Test_70_el Besòs i el Maresme/Testing Plane ID/"
base_export_path = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Results/Test_70_el Besòs i el Maresme/Testing Plane Information/Images/"

for experiment in tqdm.tqdm(os.listdir(base_path)):
# experiment = "GradientDBSCAN_distance_threshold_0.5__squareSize_0.5_polar_False_DBSCANeps_0.1_DBSCANminSamples_4"

    fig, axes = plt.subplots(3, 3, figsize=(15, 15), dpi=200)
    axes = axes.flatten()

    experiment_folder = base_path + experiment + "/"
    for idx, parcel in enumerate([x for x in os.listdir(experiment_folder) if os.path.isdir(experiment_folder+x)]):
        parcel_folder = experiment_folder + parcel + "/"
        for laz_file in os.listdir(parcel_folder):
            lasDF = laspy.read(parcel_folder + laz_file)
            x = lasDF.x
            y = lasDF.y
            classification = lasDF.classification
            classification = np.where(classification == 255, -1, classification)

            scatter = axes[idx].scatter(x, y, c=classification, cmap='viridis', s=1, alpha=0.6)
            axes[idx].set_title(parcel)
            axes[idx].set_xlabel("x")
            axes[idx].set_ylabel("y")
            axes[idx].set_aspect("equal")

    # Adjust layout and show the plot
    export_path = base_export_path + experiment + ".png"
    fig.suptitle(experiment)
    plt.savefig(export_path, dpi=200)
    plt.close()