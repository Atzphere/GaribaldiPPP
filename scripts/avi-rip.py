import skvideo
import skvideo.io
import os


def getParentDir(directory):
    return os.path.dirname(directory)


current_dirs_parent = getParentDir(os.getcwd())
videos = current_dirs_parent + "\\data\\Test Plot Photos"
export = current_dirs_parent + "\\export"
ffmpeg_path = current_dirs_parent + "\\ffmpeg_1.4\\bin"
skvideo.setFFmpegPath(ffmpeg_path)



def getFilesWIthPaths(dir):
    to_process = os.listdir(dir)
    c = 0
    for i in to_process:
        to_process[c] = dir + "\\" + i
        c += 1
    return to_process


def aviToImage(file, output):
    frames = skvideo.io.vreader(file)
    i = 0
    for frame in frames:
        skvideo.io.vwrite(
            output + "\\" + os.path.basename(file) + str(i) + ".png", frame)
        i += 1


for video in getFilesWIthPaths(videos):
    aviToImage(video,export)
