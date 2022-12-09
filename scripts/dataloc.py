reference = open("FILEPATHS.txt", "r")
lines = f.readlines()

cameras = lines[0]
export = lines[1]
invalids = lines[2]
dupes = lines[3]
