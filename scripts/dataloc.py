'''
Convenient way to change data directories for all scripts globally
intead of going into each one and changing a directory constant.
'''
reference = open("FILEPATHS.txt", "r")
lines = f.readlines()

videos = lines[0]
export = lines[1]
cameras = lines[2]
invalids = lines[3]
dupes = lines[4]
