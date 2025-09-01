import numpy as np
from sklearn.linear_model import LinearRegression

def planarSilhouette(X, labels):
    # Fit a plane for each group of labels
    planes = []
    uniqueLabels, inverse = np.unique(labels, return_inverse=True)
    for label in np.unique(labels[labels!= -1]):
        mask = (labels == label)
        subsetX = X[mask]
        plane = LinearRegression().fit(subsetX[:,0:2], subsetX[:,2])
        planes.append(plane)

    # Drop planes with a -1 label
    mask = (labels != -1)
    actualInliers = X[mask]
    
    # Create outlierPlane
    mask = (labels == -1)
    unassigned = X[mask]
    if(unassigned.shape[0] >= 3):
        outlierPlane = LinearRegression().fit(unassigned[:,0:2], unassigned[:,2])
        planes.append(outlierPlane)

    # if dataset if empty, return 0
    if(len(actualInliers) == 0):
        return 0
    
    # if there's only a plane and no outliers, return 0 (we don't trust it)
    if(len(uniqueLabels) == 1):
        return 0

    silhouette_list = []
    for label in np.unique(labels[labels!= -1]):
        mask = (labels == label)
        planeInliers = X[mask]
        

        ###################
        ### PLACEHOLDER
        # silhouette_list.append(0)
        ####################

        for inlier in planeInliers:
            # compute all vertical distances from a point to every plane
            distances = np.zeros(len(planes))
            for plane_idx in range(len(planes)):
                distances[plane_idx] = abs(inlier[2] - planes[plane_idx].predict([inlier[0:2]])[0])

            a = distances[label]

            # and the next closest as the neighbor distance (b_i)        
            mask = np.ones_like(distances, dtype=bool)
            mask[label] = False  
            neighborDistances = distances[mask]
            if len(neighborDistances) == 0:
                b = np.inf
                silhouette_list.append(0)
            elif len(neighborDistances) == 1:
                b = neighborDistances
                # Compute silhouette
                individual_s = (b - a) / np.maximum(b, a)
                silhouette_list.append(individual_s)
            else:
                b = np.min(neighborDistances)
                # Compute silhouette
                individual_s = (b - a) / np.maximum(b, a)
                silhouette_list.append(individual_s)

    return np.mean(silhouette_list)