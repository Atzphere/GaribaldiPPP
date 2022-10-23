import skvideo
import skvideo.io
import os


def getParentDir(directory):
    return os.path.dirname(directory)


current_dirs_parent = getParentDir(os.getcwd())
cameras = current_dirs_parent + "\\data\\cameras" # folder containing individual camera folders
dest = current_dirs_parent + "\\export" # export folder
ffmpeg_path = current_dirs_parent + "\\ffmpeg_1.4\\bin"
print(ffmpeg_path)
skvideo.setFFmpegPath(ffmpeg_path)



def getFilesWIthPaths(dir): # get list of file paths to process
    to_process = os.listdir(dir)
    c = 0
    for i in to_process:
        to_process[c] = dir + "\\" + i
        c += 1
    return to_process

# cull: only take the images in the sequence at the indices indicated

def aviToImage(file, output, cull=[]): 
    frames = skvideo.io.vreader(file)
    i = 0

    for frame in frames:
        if ((not cull) or (i in cull)):
            skvideo.io.vwrite(
                output + "\\" + os.path.basename(file) + str(i) + ".png", frame)
        i += 1


def folderAviToImage(folder,output,cull=[]): #folder containing AVIs -> output folder
    videos = getFilesWIthPaths(folder)
    globalCounter = 0
    fileCounter = 1

    for video in videos:
        frames = skvideo.io.vreader(video)
        localCounter = 0
        print("Processing " + os.path.basename(video) + 
        " (" + str(fileCounter) + " of " + str(len(videos)) + ")")

        for frame in frames:
            if ((not cull) or (localCounter in cull)):
                skvideo.io.vwrite(
                    output + format(globalCounter, "0" + "5") + ".png", frame)
                globalCounter += 1

            localCounter += 1
        fileCounter += 1
'''
Get list of camera folders
For every camera folder: grab the nth frame(s) of every video file, put it into the respective camera output folder.

'''

''' 
for camera in getFilesWIthPaths(cameras):
    videos = getFilesWIthPaths(camera + "\\100MEDIA")  
    export = dest + "\\" + cameraName
    i = 1
    print("Starting processing: " + cameraName)

    if (os.path.exists(export)):
        print("Output folder already exists: " + export + ", writing to folder.")
    else:
        os.mkdir(export)
        print("Created output folder " + export)

    for video in videos:
        print("Processing " + os.path.basename(video) + 
            " (" + str(i) + " of " + str(len(videos)) + ")")
        aviToImage(video, export, [2])
        i += 1
'''

# for fully processing a single camera
camera = "C:\\Users\\allen\\Documents\\ITEX\\GaribaldiPPP\\data\\Sentinel_bay_towards_glacier_april-july_2022"
videos = getFilesWIthPaths(camera + "\\100MEDIA")
cameraName = os.path.basename(camera)
export = dest + "\\" + cameraName + "FULL"
print("Starting processing: " + cameraName)

if (os.path.exists(export)):
    print("Output folder already exists: " + export + ", writing to folder.")
else:
    os.mkdir(export)
    print("Created output folder " + export)

folderAviToImage(camera + "\\100MEDIA",export + "\\CASS_10W_",[])
