import skvideo
import skvideo.io
import os
import numpy as np
import multiprocess as mp
# from matplotlib import pyplot as plt
import dirtools
import dataloc
import psutil

# only get the first 9 frames

keep_frame_num = -1

project_home = dirtools.get_parent_dir(os.getcwd(), depth=2)
os.chdir(project_home)
workingdir = os.getcwd()
camera_dir = dataloc.videos
output_dir = dataloc.export
errorNoColor = np.zeros((300, 300, 3))
errorNoColor[:, :, 0] = 255

problematics = {}  # date offsets


def avi_to_imgseq(avi, numframes=keep_frame_num):
    '''
    Returns a generator object of videos that can be iterated over
    i.e. to write to file, etc.

    Takes the path of a video file (we use avi for our phenocams)
    numframes: int, number of frames to read, keep to bare minimum for
    fastest performance

    if numframes is -1, process the entire video file.

    Parameters:
        avi (path str) : the filepath of an avi file.

        numframes (int) : the number of frames to get.
    '''
    print("processing {}".format(os.path.basename(avi)))
    if numframes == -1:
        return skvideo.io.vreader(avi)  
    else:
        return skvideo.io.vreader(avi, num_frames=numframes)


def is_grayscale(frame, samplex=5, sampley=5):
    '''
    Tries to determine if a given frame is grayscale.
    Does this by sampling regularly spaced pixels a given amount of times
    if all these samples are monochrome, return True, else false.

    Samples a total of samplex * sampley points.

    Parameters:
        frame (ndarray) : a numpy image array with shape (x, y, 3)

        samplex, sampley (int) : the amount of sample points on each axis.
                                 this function uses meshgrid to generate a 
                                 grid of sample points using these.
    '''

    frame_width = np.size(frame, 0)
    frame_height = np.size(frame, 1)
    x_sample_pts = np.around(np.linspace(
        0, frame_width - 1, samplex)).astype(int)
    y_sample_pts = np.around(np.linspace(
        0, frame_height - 1, sampley)).astype(int)

    x, y = np.meshgrid(x_sample_pts, y_sample_pts)
    # plt.scatter(x, y)
    samples = frame[x, y, :]
    # print(samples)
    truthsRG = samples[:, :, 0] == samples[:, :, 1]
    truthsGB = samples[:, :, 1] == samples[:, :, 2]
    return np.all([truthsRG, truthsGB])


def get_colored_images(frames, cname):
    '''
    Gets all non-B&W images in an image sequence.
    Useful for daylight detection from the phenocams - they
    automatically switch from infrared (B&W) imaging to color
    when ambient light is high enough.

    We want this because the earlier in the day we take images,
    the lower the contrast from shadows is and the lower the contrast.

    Parameters:
        frames : arraylike of ndarrays with shape (x, y, 3)
                 where x, y are image dimensions and the 3-array contains RGB
                 Example: a pure-black 100x100px image would be
                 np.zeros((100, 100, (0, 0, 0)))

                 This format is naturally returned by avi_to_imgseq()

    '''
    print("processing frames...")
    colored_frames = []
    for frame in frames:
        if not is_grayscale(frame):
            colored_frames.append(frame)
    print("...done")
    print("RAM % used:", psutil.virtual_memory()[2])
    print(dir())
    if len(colored_frames) != 0:
        return colored_frames
    else:
        print("FRAME PROCESSING: NO COLORED FRAMES FOUND FOR A FILE")
        return [errorNoColor]

    camera_name = os.path.basename(cname)

    newpath = output + "/" + camera_name

    if not os.path.exists(newpath):
        os.makedirs(newpath)
        print("Created output folder for camera {cname}".format(
            cname=camera_name))
    else:
        print("Output folder {cname} already exists, using this.".format(
            cname=camera_name))

    for day, frames in enumerate(results):
        newpath_day = new=ath + "/day{num:03d}".format(num=day)
        if not os.path.exists(newpath_day):
            os.makedirs(newpath_day)
            print("Created output folder for camera {cname} day {day}".format(
                cname=camera_name, day=day))
        else:
            print("Output folder already exists, using this.")
        for index, frame in enumerate(frames):
            skvideo.io.vwrite(newpath + "/{cname}_day{date:03d}_{num:03d}_.jpg".
                              format(cname=camera_name,
                                     date=(day + date_offset),
                                     num=(index)), frame)


# plt.imshow(get_first_colored(avi_to_imgseq("C:\\Users\\allen\\Documents\\Garibaldi ITEX\\Garibaldi_phenocams_Sept_2022\\Plot_photos\\CASS_Plot_photos_Aug9_2022\\CASS_9C\\100MEDIA\\DSCF0010.AVI")))
# plt.show()


def process_camera(camera_folder, data_folder="/100MEDIA/",
                   output=output_dir, numframes=keep_frame_num, date_offset=0,
                   custom_file_name=""):
    '''
    Procceses a camera folder i.e. CASS_10W by going into its
    image data folder (default is /100MEDIA/ on Apeman cameras)
    and writing all non-grayscale images from each video file
    in chronological order to the output directory in a folder
    with the same name as camemra_folder unless a custom_output_name
    is specified.

    Encodes date metadata since first image i.e. day 1, day 2 etc.
    DEPRECATED FEATURE - now done in build_metadata.

    Parameters:
        camera_folder (path str) : folder path for a camera

        data_folder (non-absolute path str) : folder in camera_folder w/ data

        output (path) : output director

        numframe (int) : number of frames to search for a colored image in

        date_offset (int) : number to offset a given camera's start date by
                            useful for when one camera is behind

        custom_output_name (str) : name to give to output files.
                                   Defaults to the camera folder name.

    '''
    camera_name = os.path.basename(camera_folder)

    source = camera_folder + data_folder

    '''
    generate worklist of files to process, resorting stuff to
    account for some cameras bugging out and restarting their counts.
    '''
    files = dirtools.get_files(source)
    # weird hack to deal with brackets (duplicate files from number overflow
    # should be last)
    sort_template = map((lambda f: ("zzzzz" + f) if "(" in f else f), files)
    files_sorted = [s for _, s in sorted(
        zip(sort_template, files), key=lambda pair: pair[0])]

    video_worklist = dirtools.get_files(source, fullpath=True)
    # print("video worklist: {v}".format(v=video_worklist))

    print("processing {cname} ({num} files)".format(
        cname=camera_name, num=len(video_worklist)))

    def func_wrapper(path):
        '''
        needed to get around pickling issues with multiprocessing & lambda

        '''
        return get_colored_images(avi_to_imgseq(path, numframes), path)

    p.map(func_wrapper, video_worklist)

    print("videos processed, writing to files...")


'''
    for index, frame in enumerate(results):
        # NEED TO CHANGE THIS TO HANDLE MULTIPLE IMAGES/DAY
        # RESULTS IS LIST OF LIST OF IMAGES ATM
        skvideo.io.vwrite(newpath + "/{cname}_[{num:03d}].jpg".
                          format(cname=camera_name,
                          num=(index + date_offset)), frame)
'''

'''
Everything works!
Todo:
Add day number padding - makes sorting easier

More verbose processing

Write greenness stuff

Look into possible dir creation thing not working as wanted?

'''

if __name__ == "__main__":
    print("working in {dir}".format(dir=project_home))
    print("target directory: {dir}".format(dir=output_dir))
    print("cameras folders found: {cams}\n ({num} total)"
          .format(cams=dirtools.get_subdirs(camera_dir), num=len(dirtools.get_subdirs(camera_dir))))

    print("generating worklist to process...")
    worklist = dirtools.get_subdirs(camera_dir, fullpath=True)
    # print(worklist)

    process_count = mp.cpu_count()
    print("starting process pool: {num} workers.".format(num=process_count))
    p = mp.Pool(process_count)
    print("started")
    for camera in worklist:
        try:
            if os.path.basename(camera) in problematics.keys():
                process_camera(
                    camera, date_offset=problematics[os.path.basename(camera)])
            else:
                process_camera(camera)
        except:
            print("something went wrong with {cam}".format(
                cam=os.path.abspath(camera)))
    p.close()
    p.join()
    print("finished.")
