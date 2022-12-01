import skvideo
import skvideo.io
import os

# only get the first 9 frames


def getParentDir(directory, depth=1):
    path = directory
    for i in range(0, depth):
        path = os.path.dirname(path)
    return path


'''
new procedure:
execute bash script to get manifest list of files in order for each camera - place this in each directory
follow this file order instead of cameras 
only get the first x frames 
quantify light by getting average brightness


'''

project_home = getParentDir(os.getcwd(), depth=2)
camera_dir = project_home + "/Garibaldi_phenocams_Sept_2022/"

print("working in {dir}".format(dir=project_home))
print([x[0] for x in os.walk(camera_dir)])
print("generating worklist to process...")