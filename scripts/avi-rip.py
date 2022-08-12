import skvideo
import skvideo.io
import os


def getParentDir(directory):
    return os.path.dirname(directory)


current_dirs_parent = getParentDir(os.getcwd())
cameras = current_dirs_parent + "\\data\\Cameras" # folder containing individual camera folders
dest = current_dirs_parent + "\\export" # export folder
ffmpeg_path = current_dirs_parent + "\\ffmpeg_1.4\\bin"
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


'''
Get list of camera folders
For every camera folder: grab the nth frame(s) of every video file, put it into the respective camera output folder.

''' 
for camera in getFilesWIthPaths(cameras):
    videos = getFilesWIthPaths(camera)
    export = dest + "\\" + os.path.basename(camera)
    os.mkdir(export)
    for video in videos:
        aviToImage(video, export, [2])
