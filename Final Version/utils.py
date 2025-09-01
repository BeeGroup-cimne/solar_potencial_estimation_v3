import os
import shutil

def create_output_folder(directory, deleteFolder = False):
    if not(os.path.isdir(directory)):
        os.makedirs(directory)
    else:
        if(deleteFolder):
            shutil.rmtree(directory)
            os.makedirs(directory)

def copy_folder(sourceFolder, targetFolder):
    if os.path.exists(targetFolder):
        confirmation = input("\nThis folder already exists, do you want to delete its contents? (Y or y for yes, anything else for no) \n\n")
        if confirmation.upper() == "Y":
            shutil.rmtree(targetFolder)
            shutil.copytree(sourceFolder, targetFolder)
            print("Folder copied!")
            return
        else:
            print("Folder not copied.")
    else:
        shutil.copytree(sourceFolder, targetFolder)
    