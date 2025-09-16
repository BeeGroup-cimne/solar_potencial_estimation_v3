import geopandas as gpd
import matplotlib.pyplot as plt
import __getMetrics
import pandas as pd
import os
import re

def plot_identified_planes(experimentPath, parcel, construction):
    parcelPath = experimentPath + "/" + parcel + "/"
    constructionPath = parcelPath + str(construction) + "/"
    gpkgPath = constructionPath + "Plane Identification/" + construction + ".gpkg"
    geoDF = gpd.read_file(gpkgPath)
    geoDF.plot(column = "cluster", legend = True)
    plt.show()

def plot_parcel_planeID(experimentPath, parcel):
    pass

def plot_yearly_panels(experimentPath, parcel, construction):
    parcelPath = experimentPath + "/" + parcel + "/"
    constructionPath = parcelPath + str(construction) + "/"

    fig, ax = plt.subplots()

    gpkgPath = constructionPath + "Solar Estimation Panels Simulated/" + construction + ".gpkg"
    geoDF = gpd.read_file(gpkgPath)
    geoDF.plot(column = "yearly", legend = True, cmap="inferno", ax=ax)
    cadasterPath = constructionPath + "Map files/" + construction + ".gpkg"
    cadasterGDF = gpd.read_file(cadasterPath)
    cadasterGDF.plot(facecolor="none", edgecolor="black", ax=ax)
    plt.show()


def experiments_box_plots(expClass, expList, resultsPath):
    
    silhouetteVectorList = []
    for metricsFile in expList:
        metricsDF = pd.read_csv(resultsPath + metricsFile)
        groupedMetrics = __getMetrics.group_by_constructions(metricsDF)
        silhouetteVectorList.append(groupedMetrics["avg_silhouette"].values)
    

    num_iterations = []
    for text in expList:
        match = re.search(r"num_iterations_(.*?)_Metrics", text)
        num_iterations.append(match.group(1))

    inlierThreshold = []
    for text in expList:
        match = re.search(r"inlierThreshold_(.*?)_num_iterations", text)
        inlierThreshold.append(match.group(1))

    boxPlotDF = pd.DataFrame({"silhouette": silhouetteVectorList, "num_iterations": list(map(int,num_iterations)), "inlierThreshold": inlierThreshold})
    boxPlotDF["inlierThreshold"] = [float(s.replace("p",".")) for s in boxPlotDF["inlierThreshold"]]
    boxPlotDF = boxPlotDF.sort_values(by = ["inlierThreshold", "num_iterations"])

    print(boxPlotDF["inlierThreshold"] )


    fig, ax = plt.subplots()
    boxplot = ax.boxplot(boxPlotDF["silhouette"], tick_labels=boxPlotDF["num_iterations"], patch_artist=True)

    unique_thresholds = sorted(boxPlotDF["inlierThreshold"].unique())
    color_map = dict(zip(unique_thresholds, plt.cm.tab10.colors[:len(unique_thresholds)]))

    for patch, thr in zip(boxplot['boxes'], boxPlotDF["inlierThreshold"]):
        patch.set_facecolor(color_map[thr])

    # colors = ["blue", "blue", "darkred", "darkred"]
    # for i, patch in enumerate(boxplot['boxes']):
    #     patch.set_facecolor(colors[i % 4])  # alternate colors

    for median in boxplot['medians']:
        median.set(color='black')

    last_thr = None
    for i, (patch, thr) in enumerate(zip(boxplot['boxes'], boxPlotDF["inlierThreshold"])):
        if thr != last_thr:  # only label the first of consecutive repeats
            y = max([line.get_ydata().max() for line in boxplot['whiskers'][2*i:2*i+2]])
            ax.text(i + 1, 1.1 + 0.02, f"{thr}", ha="center", va="bottom", fontsize=9)
        last_thr = thr

    plt.title(expClass, pad=25)
    plt.show()

if __name__ == "__main__":

    wd = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Final Version/"
    resultsPath = wd + "Results/"
    experimentPath = resultsPath + "Experiment 1/"
    parcel = "4054901DF3845C"
    construction = "115084364"

    plot_yearly_panels(experimentPath, parcel, construction)

    # metricsFilePath = "planeExtract_distance_threshold_0p5_inlierThreshold_0p15_num_iterations_50_Metrics.txt"
    # metricsFile = resultsPath + metricsFilePath 

    # expClass = "kPlanes"
    # expList =  [x for x in os.listdir(resultsPath) if (os.path.isfile(resultsPath+x) and x.startswith(expClass) and x.endswith("Metrics.txt"))]
    # experiments_box_plots(expClass, expList, resultsPath)