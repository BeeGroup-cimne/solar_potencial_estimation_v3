import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
import laspy
from shapely.geometry import MultiPolygon, Polygon
from sklearn.linear_model import LinearRegression
from sklearn.metrics import root_mean_squared_error
import math
from sklearn.cluster import DBSCAN


class ClusterPipeline:
    def __init__(self, clustering_stages):
        self.clustering_stages = clustering_stages # Each stage is a clustering class

    def fit(self, X, y=None):
        self.stage_labels = []
        self.final_labels = np.zeros(X.shape[0], dtype=str)
        
        current_data = X 
        current_labels = np.zeros(X.shape[0], dtype=int)  # Initialize labels
        cluster_offset = 0

        for stage in self.clustering_stages:
            
            new_labels = np.full(len(current_labels), -1)  # New labels for this stage
            # new_labels = np.zeros_like(current_labels)  # New labels for this stage
            unique_clusters = np.unique(current_labels)  # Unique clusters in current stage
            unique_clusters = unique_clusters[unique_clusters != -1]
            
            
            for cluster_id in unique_clusters:
                

                cluster_data = current_data[current_labels == cluster_id]
                if len(cluster_data) < 3:  # Skip small clusters
                    continue
                
                # Fit the clustering algorithm to the current cluster
                stage.fit(cluster_data)
                cluster_stage_labels = stage.labels_
                cluster_offset += len(np.unique(cluster_stage_labels)) # Update cluster offset for the next unique label
                
                # Assign new labels offset by cluster_offset
                new_labels[(current_labels == cluster_id) & (current_labels != -1)] = (cluster_stage_labels + cluster_offset)
                
                
            # Store the stage labels and update current labels
            self.stage_labels = new_labels.copy()
            current_labels = new_labels
            
        self.final_labels = self.stage_labels
        min_label = min([label for label in self.stage_labels if label != -1])
        self.final_labels = [(label - min_label if label != -1 else -1) for label in self.stage_labels]
        return self
    
    def getAllPlanes(self, X):
        planes = []
        for cluster in np.unique(self.final_labels):
            # if cluster != -1:
            planes.append(LinearRegression().fit(X[np.where(self.final_labels == cluster)[0], 0:2], X[np.where(self.final_labels == cluster)[0],2]))
        self.planes = planes
        return self

class HeightSplit():
    def __init__(self, distance_threshold=0.45):
        self.distance_threshold = distance_threshold
        
    def fit(self, X):
        self.heightChanges = []
        n_samples, n_features = X.shape

        reorder = X[:, 2].argsort() 
        X = X[reorder]
        
        deltaZ = np.diff(X[:,2], prepend=0)
        
        labels = np.zeros_like(deltaZ, dtype=int)

        current_label = 0
        for i in range(1, len(deltaZ)):
            if deltaZ[i] > self.distance_threshold:
                current_label += 1
                self.heightChanges.append(X[i-1,2])
            labels[reorder[i]] = current_label

        self.labels_ = labels
        # print("Split into", len(np.unique(self.labels_)), "heightgroups.")
        return self

    def predict(self, X):
        pass

    def fit_predict(self, X, y=None):   
        pass

class PlanesCluster():
    def __init__(self, inlierThreshold=0.15, num_iterations=10, minPlanes=2, maxPlanes=20, iterationsToConverge=10, useDistanceSampling=True):
        self.inlierThreshold = inlierThreshold
        self.num_iterations = num_iterations
        self.minPlanes = minPlanes
        self.maxPlanes = maxPlanes
        self.iterationsToConverge = iterationsToConverge
        self.useDistanceSampling = useDistanceSampling

    def sampleCentroid(self, X, n_planes):
        centroids = np.zeros((n_planes, X.shape[1]))
        index = np.random.choice(X.shape[0], 1)
        centroids[0, :] = X[index,:]
        distances = np.zeros((X.shape[0], n_planes-1))
        for i in range(1, n_planes):
            if(self.useDistanceSampling):
                distances[:, i-1] = (np.linalg.norm(X[:,:] - centroids[i-1,:], axis=1))
                average_distances = distances.mean(axis=1)
                normalized_distances = average_distances / average_distances.sum()
                selected_index = np.random.choice(len(X), p=normalized_distances)
            else:
                selected_index = np.random.choice(len(X))
            centroids[i, :] = X[selected_index,:]
        return centroids
        
    def sample2Coplanar(self, X, centroids):
        triplets = np.zeros((centroids.shape[0], X.shape[1], 3)) # n_planes * 3 coordinates * 3 points/plane
        for i in range(len(centroids)):
            if(self.useDistanceSampling):
                triplets[i, 0, :] = centroids[i]
                distances = np.linalg.norm(X[:,:] - centroids[i,:], axis=1)
                closeness = distances.max() - distances
                probabilities = closeness / closeness.sum()
                selected_indexes = np.random.choice(len(X), 2, p=probabilities)
            else:
                selected_indexes = np.random.choice(len(X), 2)
            triplets[i, 1:3, :] = X[selected_indexes,:]
        return triplets

    def fit(self, X):
        best_score = -np.inf
        best_labels = []    
        best_planes = []

        scores_ = []
        for n_planes in range(self.minPlanes, self.maxPlanes+1):
            score = -np.inf
            best_score_n = -np.inf
            best_labels_n = []    
            best_planes_n = []

            for i in range(self.num_iterations):
                # Sample points and get planes
                centroids = self.sampleCentroid(X, n_planes)
                triplets = self.sample2Coplanar(X, centroids)

                planes = []
                for triplet in triplets:
                    reg = LinearRegression().fit(triplet[:,0:2], triplet[:,2])
                    planes.append(reg)
                
                # Compute distances and find inliers
                distances = np.zeros((X.shape[0], len(planes)))
                for plane_idx in range(len(planes)):
                    distances[:, plane_idx] = abs(X[:,2] - planes[plane_idx].predict(X[:,0:2]))
                labels = np.argmin(distances, axis=1)

                selected_distances = np.array([distances[i, idx] for i, idx in enumerate(labels)])
                labels[np.where(selected_distances > self.inlierThreshold)[0]] = -1
                
                lastLabels = labels
                oldPlanes = planes
                for j in range(self.iterationsToConverge):
                    planes = []
                    for k in range(n_planes):
                        try:
                            reg = LinearRegression().fit(X[np.where(labels == k)[0],0:2], X[np.where(labels == k)[0],2])
                            planes.append(reg)
                        except:
                            pass
                    distances = np.zeros((X.shape[0], len(planes)))

                    for plane_idx in range(len(planes)):
                        distances[:, plane_idx] = abs(X[:,2] - planes[plane_idx].predict(X[:,0:2]))
                    labels = np.argmin(distances, axis=1)

                    selected_distances = np.array([distances[i, label] for i, label in enumerate(labels)])
                    labels[np.where(selected_distances > self.inlierThreshold)[0]] = -1
                    
                    if(np.array_equal(lastLabels, labels)):
                        break
                    else:
                        lastLabels = labels
                        oldPlanes = planes
                
                # For the same number of planes, the score will be the number of inliers
                inliers = X[np.where(labels != -1)[0]]
                score_n = len(inliers)/len(X)

                if(score_n > best_score_n):
                    best_score_n = score_n
                    best_labels_n = labels
                    best_planes_n = planes

                    labelsScore = labels[np.where(labels != -1)[0]]
                    prediction = np.zeros((inliers.shape[0]))
                    for plane_idx in range(len(planes)):
                        try:
                            prediction[np.where(labelsScore == plane_idx)[0]] = planes[plane_idx].predict(inliers[np.where(labelsScore == plane_idx)[0],0:2])
                        except:
                            pass
                    
                    # Silhouette score
                    try:
                        minIndexes = np.argmin(distances, axis=1)
                        a = selected_distances
                        
                        outerDistances = []
                        for i, row in enumerate(distances):
                            ignore_index = minIndexes[i]
                            masked_row = np.delete(row, ignore_index)
                            min_value = np.min(masked_row)
                            outerDistances.append(min_value)

                        b = np.array(outerDistances)
                        diffTerm = b-a
                        maxTerm = np.maximum(b, a)
                        individual_silhouette = diffTerm/maxTerm
                        score = 1/len(X)*np.sum(individual_silhouette)
                    except:
                        score = len(inliers)


            if(score > best_score):
                best_score = score
                best_labels = best_labels_n
                best_planes = planes

        self.score = best_score 
        self.labels_ = best_labels
        self.planes = best_planes
        return self

    def predict(self, X):
        pass

    def fit_predict(self, X, y=None):
        pass

class GradientCluster():
    def __init__(self, squareSize=1, polar=True, scaleFactorMagnitude=1, scaleFactorAngle=1, DBSCANeps=1, DBSCANminSamples=8):
        self.squareSize = squareSize
        self.polar = polar
        self.scaleFactorMagnitude = scaleFactorMagnitude
        self.scaleFactorAngle = scaleFactorAngle
        self.DBSCANeps = DBSCANeps
        self.DBSCANminSamples = DBSCANminSamples

    def computeGradients(self, X):
        gradients = np.zeros((X.shape[0], 2))
        for i, (x, y, z) in enumerate(X):
            neighbors = X[ (np.abs(X[:, 0] - x) <= self.squareSize/2) & (np.abs(X[:, 1] - self.squareSize/2) <= 0.5)
            ]
            
            delta_x = neighbors[:, 0] - x
            delta_y = neighbors[:, 1] - y
            delta_z = neighbors[:, 2] - z
            
            valid_dx = delta_x != 0
            valid_dy = delta_y != 0
            
            # Compute sum(deltaZ / deltaX) and sum(deltaZ / deltaY)
            sum_dz_dx = np.sum(delta_z[valid_dx] / delta_x[valid_dx])
            sum_dz_dy = np.sum(delta_z[valid_dy] / delta_y[valid_dy])
            
            # Store the gradient
            gradients[i] = [sum_dz_dx, sum_dz_dy]
        
        return gradients

    def fit(self, X):
        dbscan = DBSCAN(eps=self.DBSCANeps, min_samples=self.DBSCANminSamples)

        gradients = self.computeGradients(X)
        if(self.polar):
            polar_gradients = np.zeros(gradients.shape)
            polar_gradients[:, 0] = np.sqrt(gradients[:, 0]**2 + gradients[:, 1]**2)*self.scaleFactorMagnitude
            polar_gradients[:, 1] = np.arctan2(gradients[:, 1], gradients[:, 0])*180/math.pi*self.scaleFactorAngle

            dbscan.fit(polar_gradients)
        else:
            dbscan.fit(gradients)
 
        self.labels_ = dbscan.labels_
        return self
    
class PlaneExtraction():
    def __init__(self, inlierThreshold=0.15, useDistanceSampling=True, num_iterations = 20, iterationsToConverge=10, maxPlanes = 20):
        self.inlierThreshold = inlierThreshold
        self.useDistanceSampling = useDistanceSampling
        self.num_iterations = num_iterations
        self.iterationsToConverge = iterationsToConverge
        self.maxPlanes = maxPlanes

    def extractPlane(self, X, labels):
        bestScore = 0
        selectableIndices = [i for i, value in enumerate(labels) if value == -1]
        bestSelectedIndices = []
        for i in range(self.num_iterations):
            centroidIndex = np.random.choice(selectableIndices)
            centroid = X[centroidIndex, :]
            
            triplet = np.zeros((3,3)) #3 coordinates * 3 points/plane
            triplet[0, :] = centroid
            if(self.useDistanceSampling):
                try:
                    distances = np.linalg.norm(X[selectableIndices,:] - centroid[:], axis=1)
                    closeness = distances.max() - distances
                    probabilities = closeness / closeness.sum()
                    choices = np.random.choice(selectableIndices, 2, p=probabilities)
                    # triplet[1:3, :] = np.random.choice(X[selectableIndices,:], 2, p=probabilities)
                    triplet[1:3,:] = X[choices, :]
                except:
                    choices = np.random.choice(selectableIndices, 2)
                    # triplet[1:3, :] = np.random.choice(X[selectableIndices,:], 2)
                    triplet[1:3,:] = X[choices, :]
            else:
                choices = np.random.choice(selectableIndices, 2)
                # triplet[1:3, :] = np.random.choice(X[selectableIndices,:], 2)
                triplet[1:3,:] = X[choices, :]

            plane = LinearRegression().fit(triplet[:,0:2], triplet[:,2])

            # Compute distances and find inliers
            distances = abs(X[:,2] - plane.predict(X[:,0:2]))
            mask = (distances < self.inlierThreshold) & np.isin(np.arange(len(X)), selectableIndices)
            inliers = X[mask]

            oldinliers = inliers
            for j in range(self.iterationsToConverge):
                try:
                    plane = LinearRegression().fit(inliers[:,0:2], inliers[:,2])
                    distances[:] = abs(X[:,2] - plane.predict(X[:,0:2]))
                    mask = (distances < self.inlierThreshold) & np.isin(np.arange(len(X)), selectableIndices)
                    inliers = X[mask]
                    if(np.array_equal(oldinliers, inliers)):
                        break
                    else:
                        oldinliers = inliers
                except:
                    pass

            score = len(inliers)
            if(score > bestScore):
                bestScore = score
                mask = (distances < self.inlierThreshold) & np.isin(np.arange(len(X)), selectableIndices)
                bestSelectedIndices = [i for i, val in enumerate(mask) if val==True]
            
        return bestSelectedIndices
    
    def fit(self, X):
        n = 0
        labels = np.full((X.shape[0]), -1)
        looping = True
        while(looping and (n < self.maxPlanes)):
            selected_indexes = self.extractPlane(X, labels)
            labels[selected_indexes] = n
            n = n+1

            if(len(selected_indexes) <= 3):
                looping = False
            elif(len(labels[np.where(labels == -1)]) < 3):
                looping = False

        self.labels_ = labels
        return self