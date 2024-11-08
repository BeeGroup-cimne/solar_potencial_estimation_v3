def mergeLidar(lazPath, filesToMerge, outputFile):
    layersToMerge = []
    for currentfile in filesToMerge:
        directory = lazPath + str(currentfile) + ".laz"
        lidar_layer  = QgsPointCloudLayer(directory, str(currentfile), "pdal")
        layersToMerge.append(lidar_layer)

    processing.run("pdal:merge", {
        'LAYERS':layersToMerge,
        'FILTER_EXPRESSION':'',
        'FILTER_EXTENT':None,
        'OUTPUT':outputFile})

basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
lazPath = basePath + "RAW_Data/LiDAR/"
filesToMerge = [433584, 433585, 433586, 434584, 434585, 434586, 435584, 435585, 435586]
outputFile = basePath + "Data/Merged_LiDAR.laz"

mergeLidar(lazPath, filesToMerge, outputFile)
