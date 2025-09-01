import numpy as np
from sklearn.linear_model import LinearRegression
import ClusterMetrics
import utils
from tqdm import tqdm
import os
from utils import create_output_folder
import laspy
import traceback

def assign_clusters(parcelsFolder, pipeline):
    for parcel in tqdm(os.listdir(parcelsFolder), desc="Looping through parcels"):
        parcelSubfolder = parcelsFolder + parcel + "/"
        for construction in tqdm([x for x in os.listdir(parcelSubfolder) if os.path.isdir(parcelSubfolder + x)],  desc="Working on constructions", leave=False):
            constructionFolder = parcelSubfolder + construction
            create_output_folder(constructionFolder + "/Plane Identification/", deleteFolder=True)
            
            lasPath = constructionFolder + "/Map files/" + construction + ".laz"
            lasDF = laspy.read(lasPath)
            try:
                pipeline.fit(lasDF.xyz)
            except Exception as e:
                print(" ", parcel, construction, " ", e, traceback.format_exc())

            lasDF.classification  = pipeline.final_labels
            lasDF.write(constructionFolder + "/Plane Identification/"+construction+".laz")
    pass

class ClusterPipeline:
    def __init__(self, clustering_stages):
        self.clustering_stages = clustering_stages # Each stage is a clustering class

    def fit(self, X):
        self.stage_labels = []
        self.final_labels = np.zeros(X.shape[0], dtype=str)
        
        current_data = X 
        current_labels = np.zeros(X.shape[0], dtype=int)  # Initialize labels
        cluster_offset = 0

        for stage in self.clustering_stages:
            
            new_labels = np.full(len(current_labels), -1)  # New labels for this stage
            unique_clusters = np.unique(current_labels)  # Unique clusters in current stage
            unique_clusters = unique_clusters[unique_clusters != -1]
            
            cluster_offset += len(unique_clusters)

            for cluster_id in unique_clusters:
                cluster_data = current_data[current_labels == cluster_id]

                if len(cluster_data) < 5:  # Skip small clusters
                    continue

                # Fit the clustering algorithm to the current cluster
                stage.fit(cluster_data)
                cluster_stage_labels = stage.labels_
                
                # Assign new labels offset by cluster_offset
                new_labels[(current_labels == cluster_id) & (current_labels != -1)] = (cluster_stage_labels + cluster_offset)
                
                cluster_offset += len(np.unique(cluster_stage_labels)) # Update cluster offset for the next unique label
                
                
            # Store the stage labels and update current labels
            self.stage_labels = new_labels.copy()
            current_labels = new_labels
            
        self.final_labels = self.stage_labels

        arr = np.asarray(self.final_labels)
        mask = arr != -1
        unique, inv = np.unique(arr[mask], return_inverse=True)
        result = np.full_like(arr, -1)
        result[mask] = inv
        self.final_labels = result

        # min_label = min([label for label in self.stage_labels if label != -1])
        # self.final_labels = [(label - min_label if label != -1 else -1) for label in self.stage_labels]
        return self
    
class HeightSplit():
    def __init__(self, distance_threshold=0.5):
        self.distance_threshold = distance_threshold
        
    def fit(self, X):
        reorder = X[:, 2].argsort() 
        X = X[reorder]
        
        deltaZ = np.diff(X[:,2], prepend=0)

        labels = np.zeros_like(deltaZ, dtype=int)
        current_label = 0
        for i in range(1, len(deltaZ)):
            if deltaZ[i] > self.distance_threshold:
                current_label += 1
            labels[reorder[i]] = current_label

        self.labels_ = labels
        return self

class PlaneExtraction():
    def __init__(self, inlierThreshold=0.15, useDistanceSampling=True, num_iterations = 20, iterationsToConverge=10, maxPlanes = 20):
        self.inlierThreshold = inlierThreshold
        self.useDistanceSampling = useDistanceSampling
        self.num_iterations = num_iterations
        self.iterationsToConverge = iterationsToConverge
        self.maxPlanes = maxPlanes

    def __extractPlane(self, X, labels):
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
                    triplet[1:3,:] = X[choices, :]
                except:
                    print("Distance sampling could not be performed, random points are selected instead")
                    choices = np.random.choice(selectableIndices, 2)
                    triplet[1:3,:] = X[choices, :]
            else:
                choices = np.random.choice(selectableIndices, 2)
                triplet[1:3,:] = X[choices, :]

            plane = LinearRegression().fit(triplet[:,0:2], triplet[:,2])

            # Compute distances and find inliers
            distances = abs(X[:,2] - plane.predict(X[:,0:2]))
            # a, b, c, d = plane.coef_[0], plane.coef_[1], -1, plane.intercept_
            # distances = np.abs(a * X[:, 0] + b * X[:, 1] + c * X[:, 2] + d) / np.sqrt(a**2 + b**2 + c**2)
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
                    print("Plane refitting could not be performed after " + str(j) + " iterations")

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
            selected_indexes = self.__extractPlane(X, labels)
            labels[selected_indexes] = n
            n = n+1

            if(len(selected_indexes) <= 3):
                looping = False
            elif(len(labels[np.where(labels == -1)]) < 3):
                looping = False

        self.labels_ = labels
        return self
    
class kPlanes():
    def __init__(self, inlierThreshold=0.15, num_iterations=10, minPlanes=1, maxPlanes=20, iterationsToConverge=10, useDistanceSampling=True):
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
                finalPlanes = planes

                # repeat until convergence
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
                        finalPlanes = planes
                
                ### COMPUTE SCORE #####################################################################
                print("HERE")
                score = ClusterMetrics.planarSilhouette(X, labels)
                if(score > best_score_n):
                    best_score_n = score
                    best_labels_n = lastLabels
                    best_planes_n = finalPlanes
                print("HERE2")
            ### COMPARE SCORES AND KEEP BEST #####################################################################
            if(best_score_n > best_score):
                best_score = best_score_n
                best_labels = best_labels_n
                best_planes = best_planes_n
            
        self.score = best_score 
        self.labels_ = best_labels
        self.planes = best_planes
        return self