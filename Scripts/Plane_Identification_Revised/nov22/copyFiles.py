import os
import shutil

source_directory = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Results/Test_70_el Besòs i el Maresme/Testing Plane ID/" 
destination_directory = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Results/Test_70_el Besòs i el Maresme/Testing PlaneInformation/"
destination_directory = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Results/Test_70_el Besòs i el Maresme/Testing Plane Information/Summaries/"
# os.makedirs(destination_directory, exist_ok=True)

# Iterate through each folder in the main directory
for folder_name in os.listdir(source_directory):
    print(folder_name)
    folder_path = os.path.join(source_directory, folder_name)
    
    if os.path.isdir(folder_path):
        metrics_file = os.path.join(folder_path, "Summary.csv")

        new_metrics_file = os.path.join(destination_directory, f"{folder_name}_Summary.csv")
        
        if os.path.exists(metrics_file):
            shutil.copy(metrics_file, new_metrics_file)


print("Files copied and renamed successfully!")
