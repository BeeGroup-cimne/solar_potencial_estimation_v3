import json
import pandas as pd
import numpy as np
import csv
import os
import math
import shutil 
from tqdm import tqdm

import geopandas as gpd
import laspy

import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
from matplotlib.cm import ScalarMappable
from mpl_toolkits.axes_grid1 import make_axes_locatable
from PIL import Image 

from matplotlib.colors import Normalize, ListedColormap, BoundaryNorm
import matplotlib.colors as mcolors

import numpy as np
import math
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import griddata
from scipy.spatial import cKDTree

import warnings
warnings.filterwarnings('ignore')

def create_output_folder(directory, deleteFolder = False):
    if not(os.path.isdir(directory)):
        os.makedirs(directory)
    else:
        if(deleteFolder):
            shutil.rmtree(directory)
            os.makedirs(directory)


basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
# neighborhood = "70_el Besòs i el Maresme"
neighborhood = "Test_70_el Besòs i el Maresme"
parcelsFolder = basePath + "/Results/" + neighborhood + "/Parcels/"
scalebar = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Scripts/ReportGeneration/Scale_250.png"

def get_location_info(construction, constructionFolder):
    # Load gpkg
    cadasterPath = constructionFolder + "/Map files/" + construction + ".gpkg"
    cadasterGDF = gpd.read_file(cadasterPath)
    area = cadasterGDF.geometry.area[0]
    cadasterGDF.to_crs(crs=4326, inplace=True)
    # Load Lidar
    lazPath = constructionFolder + "/Map files/" + construction + ".laz"
    lasDF = laspy.read(lazPath)

    location_info = {
        "latitude":cadasterGDF.geometry.centroid.y[0],
        "longitude": cadasterGDF.geometry.centroid.x[0],
        "area": area, #"{:.2f}".format(x)
        "lidarPoints": len(lasDF),
        "density": len(lasDF)/area
    }

    return location_info
    

def get_lidar_image(lasDF, reportFolder):
    fig, ax = plt.subplots(figsize=(6, 6)) # figsize=(12.5, 12.5), dpi=200
    ax.grid(True, 'major', 'both', alpha=0.3)
    sc = ax.scatter(lasDF.x, lasDF.y, c=lasDF.z, s=1, cmap="viridis")
    ax.set_aspect('equal', 'box')
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")

    ax.xaxis.set_major_formatter(ScalarFormatter(useOffset=True))
    ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=True))
    # ax.xaxis.set_major_locator(plt.MaxNLocator(4))

    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05)   
    cbar = plt.colorbar(sc, cax=cax)
    cbar.ax.set_title('z (m)')

    plt.tight_layout()
    fig.savefig(reportFolder + "LiDAR.png", dpi=300)
    plt.close()

def get_location_images(construction, constructionFolder, reportFolder):
    # Load gpkg
    cadasterPath = constructionFolder + "/Map files/" + construction + ".gpkg"
    cadasterGDF = gpd.read_file(cadasterPath)
    
    # Load Lidar
    lazPath = constructionFolder + "/Map files/" + construction + ".laz"
    lasDF = laspy.read(lazPath)

    get_lidar_image(lasDF, reportFolder)

def applyScaleBar(reportFolder, scalebar):
    baseFile = reportFolder + "ZoomOut.png"

    img1 = Image.open(baseFile)
    img2 = Image.open(scalebar)
    img1.paste(img2, (0,0), mask=img2)
    img1.save(reportFolder + "ZoomOut_Scaled.png")


def getPlanesImageAndInfo(construction, constructionFolder, reportFolder):
    planePath = constructionFolder + "/Plane Identification/" + construction + ".gpkg"
    planesGDF = gpd.read_file(planePath)
    
    planesGDF["ID"] = planesGDF.index
    planesGDF["area"] = planesGDF.geometry.area
    planesGDF["centroidHeight"] = planesGDF.geometry.centroid.x*planesGDF.A + planesGDF.geometry.centroid.y*planesGDF.B + planesGDF.D

    fig, ax = plt.subplots(figsize=(6, 6)) 

    # Define the number of discrete bins
    clusters = sorted(planesGDF["ID"].unique())  # Get unique cluster values
    num_clusters = len(clusters)

    # Set up the colormap and boundaries
    cmap = plt.get_cmap("rainbow", num_clusters)  # Discrete version of the colormap
    cmap = mcolors.ListedColormap(cmap(np.arange(num_clusters)), name='Pastel1_with_alpha')
    cmap.colors[:, -1] = 0.67 # Set alpha
    boundaries = np.arange(min(clusters), max(clusters) + 2)  # Create boundaries for the clusters
    norm = BoundaryNorm(boundaries, cmap.N, extend="neither")

    planesGDF.plot(
        column="ID",
        edgecolor="black",
        linewidth=1,
        cmap=cmap,
        norm=norm,
        ax=ax,
    )

    ax.grid(True, 'major', 'both', alpha=0.3)

    # Add the discrete colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])  # Required for ScalarMappable
    # cbar = fig.colorbar(sm, ax=ax, boundaries=boundaries, ticks=clusters)
    # cbar.set_label("Cluster")  # Label for the colorbar
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")

    fig.savefig(reportFolder + "PlaneID.png", dpi=300)

    planesDF = pd.DataFrame(planesGDF[["ID", "area", "tilt", "azimuth", "silhouette", "centroidHeight"]])
    planesDF["colorR"] = cmap.colors[:,0]
    planesDF["colorG"] = cmap.colors[:,1]
    planesDF["colorB"] = cmap.colors[:,2]
    planesDF["colorAlpha"] = cmap.colors[:,3]
    planesDF.to_csv(reportFolder + "PlaneID.csv", index=False)
    
def classifyPoA(allPoA):
    bins = [float('-inf'), 1350, 1400, 1450, 1500, 1550, 1600, 1650, 1700, 1750, 1800, 1850, float('inf')]
    labels = [
        '< 1350',
        '1350 - 1400',
        '1400 - 1450',
        '1450 - 1500',
        '1500 - 1550',
        '1550 - 1600',
        '1600 - 1650',
        '1650 - 1700',
        '1700 - 1750',
        '1750 - 1800',
        '1800 - 1850',
        '> 1850'
    ]

    allPoA['category'] = pd.cut(allPoA['annual'], bins=bins, labels=labels, right=False)
    
    counts = allPoA['category'].value_counts().sort_index()
    counts_df = counts.reset_index()
    counts_df.columns = ['Range', 'Area']
    return(counts_df)

def getPoAInfoImages(construction, constructionFolder, reportFolder):
    try:
        cadasterPath = constructionFolder + "/Map files/" + construction + ".gpkg"
        cadasterGDF = gpd.read_file(cadasterPath)

        allPoA = pd.DataFrame()
        poaPath = constructionFolder + "/Solar Estimation PySAM_POA_Yearly/"
        for file in os.listdir(poaPath):
            allPoA = pd.concat([allPoA, pd.read_csv(poaPath + file)], ignore_index=True)

        x = allPoA["x"]
        y = allPoA["y"]
        z = allPoA["annual"]

        # Create a grid for x and y
        xi = np.linspace(min(x), max(x), math.ceil(max(x)-min(x)))
        yi = np.linspace(min(y), max(y), math.ceil(max(y)-min(y)))
        xi, yi = np.meshgrid(xi, yi)

        # Interpolate z onto the grid
        zi = griddata((x, y), z, (xi, yi), method='linear')

        # Plot the mesh
        z_min = 1300  # Define the minimum value of the range
        zi = np.where(zi < z_min, z_min, zi)
        z_max = 1900  # Define the minimum value of the range
        zi = np.where(zi > z_max, z_max, zi)

        tree = cKDTree(np.c_[x, y])  # KDTree for distance computation
        distances, _ = tree.query(np.c_[xi.ravel(), yi.ravel()], k=1)  # Find nearest point distances
        distances = distances.reshape(xi.shape)  # Reshape to grid shape
        zi = np.ma.masked_where(distances > 2.5, zi)  # Mask zi where the distance is greater than 2m

        fig, ax = plt.subplots(figsize=(6, 6)) 
        z_levels = np.arange(z_min, z_max+1, 50)  # From 1300 to 1800 in steps of 100
        heatmap = plt.contourf(xi, yi, zi, levels=z_levels, cmap='YlOrBr_r')#YlOrBr_r

        cadasterGDF.plot(ax=ax, edgecolor="none", facecolor="none", linewidth=4)

        plt.xlabel("x (m)")
        plt.ylabel("y (m)")
        plt.grid(alpha=0.5)
        fig.savefig(reportFolder + "PoA.png", dpi=300)
        plt.close()
        
        counts_df = classifyPoA(allPoA)
        cmap = plt.get_cmap('YlOrBr_r') 
        colors = [cmap(level) for level in np.linspace(0, 1, len(z_levels)-1)]

        counts_df["colorR"] = [color[0] for color in colors]
        counts_df["colorG"] = [color[1] for color in colors]
        counts_df["colorB"] = [color[2] for color in colors]
        counts_df["colorAlpha"] = [color[3] for color in colors]

        counts_df.to_csv(reportFolder + "PoA.csv", index=False)
    except:
        print(constructionFolder)

def getPVimages(planesGDF, cadasterGDF, panelsGDF):
    fig, ax = plt.subplots(figsize=(6, 6)) 
    planesGDF.plot(ax = ax, edgecolor="black",  facecolor="none")
    cadasterGDF.plot(ax = ax, edgecolor="black", facecolor="none", linewidth=4)
    
    boundaries = np.arange(400, 601, 20)  # From 200 to 300, in steps of 20
    norm = mcolors.BoundaryNorm(boundaries, ncolors=256)
    
    im = panelsGDF.plot(ax=ax, column='yearly', edgecolor="black", legend=True,
                  cmap='gnuplot', norm=norm, legend_kwds={"label": "kWh/panel/year", "orientation": "vertical"})
    
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_aspect("equal", adjustable='box')
    plt.grid(alpha=0.5)

    for i in range(len(planesGDF)):
        centroid = planesGDF.geometry[i].centroid
        ax.annotate(str(i), (centroid.x, centroid.y), size=20, color=(0.1,0.1,0.1, 1), backgroundcolor=(1,1,1,0.65), fontname="sans-serif", fontweight="bold")

    fig.savefig(reportFolder + "PVpanels.png", dpi=300)

def getPVinfo(planesGDF, cadasterGDF, panelsGDF):
    plane_ids = []

    for panel_geom in panelsGDF.geometry:
        found_plane = None
        for idx, plane_geom in enumerate(planesGDF.geometry):
            if plane_geom.contains(panel_geom):
                found_plane = idx
                break
        plane_ids.append(found_plane)
    
    panelsGDF['plane'] = plane_ids

    bins = [float('-inf'), *np.arange(420,581,20), float('inf')]
    labels = ['< 420', *[str(i) + " - " + str(i+20) for i in np.arange(420,561, 20)], '> 580']
    
    panelsGDF['category'] = pd.cut(panelsGDF['yearly'], bins=bins, labels=labels, right=False)
    
    counts_df = (
        panelsGDF.groupby(['plane', 'category'])
        .agg(
            yearly_total=('yearly', 'sum'),
            panel_count=('yearly', 'size')
        )
        .reset_index()
    )
    
    return(counts_df)

def PVpanelsImageInfo(construction, constructionFolder, reportFolder):
    planePath = constructionFolder + "/Plane Identification/" + construction + ".gpkg"
    planesGDF = gpd.read_file(planePath)
    planesGDF["ID"] = planesGDF.index

    cadasterPath = constructionFolder + "/Map files/" + construction + ".gpkg"
    cadasterGDF = gpd.read_file(cadasterPath)

    panelsPath = constructionFolder + "/Solar Estimation Panels Simulated/" + construction + ".gpkg"
    panelsGDF = gpd.read_file(panelsPath)

    counts_df = getPVinfo(planesGDF, cadasterGDF, panelsGDF)
    counts_df = counts_df[counts_df['panel_count'] != 0].reset_index(drop=True)

    counts_df.to_csv(reportFolder + "PVpanels.csv", index=False)
    getPVimages(planesGDF, cadasterGDF, panelsGDF)
    
    
for parcel in tqdm(os.listdir(parcelsFolder), desc="Parcels", leave=True):
    # if(parcel == "4054901DF3845C"):   
        parcelSubfolder = parcelsFolder + parcel + "/"
        for construction in tqdm([x for x in os.listdir(parcelSubfolder) if os.path.isdir(parcelSubfolder + x)],  desc="Constructions", leave=False):
            # if(construction == "408"):
                constructionFolder = parcelSubfolder + construction + "/"
                reportFolder = constructionFolder + "Report Files/"
                create_output_folder(reportFolder)

                # # Get location info
                # location_info = get_location_info(construction, constructionFolder)
                # with open(reportFolder + 'location_info.json', 'w') as f:
                #     json.dump(location_info, f)

                # # Get lidar image and apply scale bar to map image
                # get_location_images(construction, constructionFolder, reportFolder)
                # applyScaleBar(reportFolder, scalebar)


                # Get id rooftops images and info
                # getPlanesImageAndInfo(construction, constructionFolder, reportFolder)

                # Get PoA info and images
                getPoAInfoImages(construction, constructionFolder, reportFolder)

                # Get PV info
                # try:
                #     PVpanelsImageInfo(construction, constructionFolder, reportFolder)
                # except:
                #     print(parcel, construction)
