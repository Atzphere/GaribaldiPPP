'''
Constructs the master greenness csv file for an entire field season's worth of data.
Multiprocessed.

Copied from a slack message below: Basically how the date counting system works.
Hopefully we don't have to do this for much longer because I will have figured out how to OCR dates from the images themselves.

Here's the current workflow I kinda have for getting date stuff:
The images from each camera are numbered sequentially to give a rough chronological order but there are occasionally multiple photos taken per day and/or days where the photos aren't good enough to run greenness extraction on.
Make two folders: INVALID and DUPES. These are global to every single camera i.e. there is no sorting.
For every camera:
Manually assign a start date to counting up from.
Go through every image by hand. If there's multiple photos taken in a day, move all but the best one into the DUPES folder. If the best photo isn't good enough to run greeness extraction i.e. because of corruption then move it into the INVALID folder
I then have a script that goes finds every image in the data, INVALID, and DUPES folders associated with a given camera and goes up through the image numbers i.e. image1, image2, ... It does things based on where it finds the next numbered photo:
If the next photo is in the data folder, extract greenness and move the date forward by one.
If the next photo is in the INVALID folder, do not extract greenness, instead returning a NaN value (so that this day is ignored when we take the average across cameras) and move the date forward by one.
If the next photo is in the DUPES folder, skip the photo and keep going until a non-DUPE photo is found.
'''
import numpy as np
import _datetime as dt
import dirtools
from PIL import Image
import csv
import multiprocess as mp
import dataloc
from collections.abc import Callable
from greenness_settings import Setting
import whitebalance

'''
REQUIREMENTS
Folder of cameras i.e. the export one produced by avi-rip.py
INVALIDS folder containing copies of invalid images
DUPES folder containing copies of duplicate images

Note: as of 3/13/2023 the dupes and invalids folders are ignored when
using the "process all images" pipeline.
'''


def poster_method_pixelCount(img, minvalue=80, maxvalue=90):
    Hue = img[:, :, 0]
    # Make mask of zeroes in which we will set greens to 1
    mask = np.zeros_like(Hue, dtype=np.uint8)

    # Set all green pixels to 1
    mask[(Hue >= minvalue) & (Hue <= maxvalue)] = 1
    return mask.mean() * 100


def GCC(img):
    red, green, blue = np.mean(img[:, :, 0]), np.mean(
        img[:, :, 1]), np.mean(img[:, :, 2])
    return (green / (red + green + blue))


def TWOG_RBi(img):
    red, green, blue = np.mean(img[:, :, 0]), np.mean(
        img[:, :, 1]), np.mean(img[:, :, 2])
    return (2 * green) - (red + blue)

# CONFIGURABLES:


global_label = "NEWMAY2023_MEAN_STDEV_50P_75P_90P_95P_2022"

'''
SETTINGS = Setting((poster_method_pixelCount,
                    GCC,
                    TWOG_RBi),
                   ("poster_method" + global_label,
                    "GCC" + global_label,
                    "2G_RBi" + global_label),
                   do_quadrants=False,
                   all_images=True,
                   percentile=75)
'''

SETTINGS = Setting((poster_method_pixelCount),
                   ("poster_method" + global_label),
                   do_quadrants=False,
                   all_images=True,
                   percentile=75)

CAMERA_DIRECTORY = dataloc.cameras
INVALIDS_DIRECTORY = dataloc.invalids
DUPES_DIRECTORY = dataloc.dupes

# this is here because I haven't gotten OCR working yet to grab dates
# the script counts up from these starts dates for every valid image.
CASS_START = dt.date.fromisoformat("2022-07-21")
SAL_START = dt.date.fromisoformat("2022-07-21")
MEAD_START = dt.date.fromisoformat("2022-08-06")

# determines what settings to apply depending on the community type:
# here the first setting is the community name and the second is the start date
# for camera recording for that community
COMMUNITY_SETTINGS = {"CASS": ("CASS", CASS_START),
                      "MEAD": ("MEAD", MEAD_START),
                      "SAL": ("SAL", SAL_START)}

# Main code below

do_quadrants = SETTINGS.do_quadrants

nan = np.nan

null_quads = (nan, nan, nan, nan)

# I want to update this to use the apeman module once I get that working


cameras = dirtools.get_subdirs(CAMERA_DIRECTORY, fullpath=True)
cameranames = dirtools.get_subdirs(CAMERA_DIRECTORY)
INVALIDS = dirtools.get_files(INVALIDS_DIRECTORY)
DUPES = dirtools.get_files(DUPES_DIRECTORY)

INVALIDS_WL = dirtools.get_files(INVALIDS_DIRECTORY, fullpath=True)
DUPES_WL = dirtools.get_files(DUPES_DIRECTORY, fullpath=True)


class Entry:
    '''
    Convenient class for representing a single line of output data
    '''
    def __init__(self, site, plot, treatment, filename,
                 date, greenness_quadrants):
        self.site = site
        self.plot = plot
        self.treatment = treatment
        self.filename = filename
        self.date = date
        self.greenness_quadrants = greenness_quadrants

    def return_csv_line(self):
        try:
            return (self.site, self.plot, self.treatment,
                    self.filename, self.date, *self.greenness_quadrants)
        except TypeError:
            return (self.site, self.plot, self.treatment,
                    self.filename, self.date, self.greenness_quadrants)

class ImagePack:
    '''
    Class that associates a given image with context (day, name, seq# etc)
    Used for multiprocessing the greenness extraction code.
    '''
    def __init__(self, img_dir, img_date):
        self.img_dir = img_dir
        self.img_date = img_date

def get_image_num(imgname, camname):
    return int(imgname.replace(camname + "_day", "").replace(".jpg", ""))


def get_day_num(dirname):
    daypos = dirname.index("day")
    return int(dirname[daypos + 3: daypos + 6])


def get_greenness_quadrants(img, extractor: Callable, itype=None, params=()):
    '''
    Extracts greenness from an image using a given method.

    Arguments:
        img : np.array Image
        the image to be analyzed

        extractor : Callable[Image -> Float]
        the function used to evaluate greenness/any other index on quadrants.

        itype : String (colorspace)
        the colorspace to convert the image to e.g. RGB, HSV...

        params : Tuple
        Parameters to be passed to the extractor i.e. threshold values.
    '''

    im = np.array((img).convert(itype))
    M = im.shape[0] // 2
    N = im.shape[1] // 2
    quadrants = [im[x:x + M, y:y + N]
                 for x in range(0, im.shape[0], M)
                 for y in range(0, im.shape[1], N)]

    quad_greenness = []

    for quadrant in quadrants:
        quad_greenness.append(extractor(quadrant, *params))

    # Now print percentage of green pixels
    return tuple(quad_greenness)


def get_greenness(img, extractor: Callable, itype=None, params=()):
    '''
    Extracts greenness from an image using a given method.

    Arguments:
        img : np.array Image
        the image to be analyzed

        extractor : Callable[Image -> Float]
        the function used to evaluate greenness/any other index on entire img

        itype : String (colorspace)
        the colorspace to convert the image to e.g. RGB, HSV...

        params : Tuple
        Parameters to be passed to the extractor i.e. threshold values.
    '''
    if type(img) is not np.ndarray:
        im = np.array((img).convert(itype))
    else:
        im = img

    return extractor(im, *params)


def get_plot_num(imgname):
    no_daynum = imgname.split("_day", 1)[0]
    pnum = ''.join(c for c in no_daynum if c.isdigit())
    return pnum


'''
img = "C:\\Users\\allen\\Desktop\\data_for_phenology\\export\\CASS_11C\\CASS_11C_day10.jpg"
test = Image.open(img).convert('HSV')
print(np.mean(get_greenness_quadrants(test)))
print(get_greenness(test))
'''


def process_camera_single_photo(zipped):
    '''
    Wrapper for processing a tuple of (camera, cameraname)
    for multiprocessing.

    Returns a list of Entry objects.
    Obsolete since we now use the entire series of photo per day
    '''
    camera, name = zipped
    entries = []
    processed_already = [] # get file names for later, remove invalid/duplicate photos
    image_names = [i for i in dirtools.get_files(camera) if "[" not in i]
    image_names.extend([i for i in INVALIDS if name in i])
    image_names.extend([i for i in DUPES if name in i])

    image_wl = dirtools.get_files(camera, fullpath=True)
    image_wl.extend([i for i in INVALIDS_WL if name in i])
    image_wl.extend([i for i in DUPES_WL if name in i])

    image_nums = [get_image_num(i, name) for i in image_names if "[" not in i]
    image_names = [x for _, x in sorted(zip(image_nums, image_names))]
    image_wl = [x for _, x in sorted(zip(image_nums, image_wl))]

    if "W" in name:
        treatment = "W"
    else:
        treatment = "C"

    for key in COMMUNITY_SETTINGS.keys():
        if key in name:
            site, start = COMMUNITY_SETTINGS[key]

    plot = get_plot_num(name)

    print("processing {}".format(name))
    date = start
    for img, imgname in zip(image_wl, image_names):
        if imgname not in processed_already:
            if imgname in INVALIDS:
                entries.append(
                    Entry(site, plot, treatment, img, date, null_quads))
                date += dt.timedelta(days=1)
                processed_already.append(imgname)
            elif imgname in DUPES:
                pass
                processed_already.append(imgname)
            else:
                img_data = Image.open(img)
                if do_quadrants:
                    entries.append(
                        Entry(site, plot, treatment, img, date,
                              get_greenness_quadrants(img_data,
                                                      poster_method_pixelCount,
                                                      "RGB",
                                                      params=(80, 90))))
                else:
                    entries.append(
                        Entry(site, plot, treatment, img, date,
                              get_greenness(img_data,
                                            poster_method_pixelCount,
                                            "RGB",
                                            params=(80, 90))))
                date += dt.timedelta(days=1)
                processed_already.append(imgname)
    return entries # OBSOLETE


def process_camera_all_photos(zipped):
    '''
    Wrapper for processing a tuple of (camera, cameraname)
    for multiprocessing. Uses new method (all photos per day)

    This is not ideal, we could see significant gains by processing individual
    or days worth of photos instead. Do something about this in the future.

    Returns a list of Entry objects.
    '''
    camera, name, method, percentile = zipped
    entries = []
    processed_already = []
    day_folders = dirtools.get_subdirs(camera, fullpath=True)
    day_nums = [get_day_num(i) for i in day_folders]

    day_folders = [x for _, x in sorted(zip(day_nums, day_folders))]

    if "W" in name:
        treatment = "W"
    else:
        treatment = "C"

    for key in COMMUNITY_SETTINGS.keys():
        if key in name:
            site, start = COMMUNITY_SETTINGS[key]

    plot = get_plot_num(name)

    print("processing {}".format(name))
    date = start
    for day in day_folders:
        values = []
        image_wl = dirtools.get_files(day, fullpath=True)
        image_names = dirtools.get_files(day, fullpath=False)
        for img, imgname in zip(image_wl, image_names):
            if imgname not in processed_already:
                img_data = Image.open(img)
                if do_quadrants:
                    values.append(get_greenness_quadrants(img_data,
                                                          method,
                                                          "RGB",))
                else:
                    values.append(get_greenness(img_data,
                                                method,
                                                "RGB",))
                processed_already.append(imgname)
                # print(type(entries))
                # print(entries)
        entries.append(Entry(site, plot, treatment, "ALL PHOTOS", date,
                             (np.mean(values),
                              np.std(values),
                              np.nanpercentile(values, 50),
                              np.nanpercentile(values, 75),
                              np.nanpercentile(values, 90),
                              np.nanpercentile(values, 95))))
        date += dt.timedelta(days=1)
    print("processing {}: ...done".format(name))
    return entries

def process_entire_camera_super_parallel(pool, camera, name, method, percentile):
    '''
    Process an entire camera's worth of photos using a given multiprocessing pool. 
    '''
    entries = []
    pack_worklist = []
    processed_already = []
    day_folders = dirtools.get_subdirs(camera, fullpath=True)
    day_nums = [get_day_num(i) for i in day_folders]

    day_folders = [x for _, x in sorted(zip(day_nums, day_folders))]

    if "W" in name:
        treatment = "W"
    else:
        treatment = "C"

    for key in COMMUNITY_SETTINGS.keys():
        if key in name:
            site, start = COMMUNITY_SETTINGS[key]
            break

    plot = get_plot_num(name)

    def process_pack(imgpack):
        img_data = whitebalance.percentile_white_balance(np.array(Image.open(imgpack.img_dir)), 90)
        img_data *= 255
        if do_quadrants:
            val = get_greenness_quadrants(img_data,
                                                  method,
                                                  "RGB",)
        else:
            val = get_greenness(img_data,
                                        method,
                                        "RGB",)
        print(val)
        # print(img_data) from when I was debugging the zeros issue
        return (imgpack.img_date, val)

    print("processing {}".format(name))
    date = start
    for day in day_folders:
        values = []
        image_wl = dirtools.get_files(day, fullpath=True)
        image_names = dirtools.get_files(day, fullpath=False)
        for img, imgname in zip(image_wl, image_names):
            if imgname not in processed_already:
                pack_worklist.append(ImagePack(img, date))
                processed_already.append(imgname)

        date += dt.timedelta(days=1)


    results = pool.map(process_pack, pack_worklist) # multiprocessed part
    collated_values = {}

    for result in results: # unpack and record the result of the pool mapping
        if result[0] not in collated_values.keys(): # if date not recorded yet
            collated_values.update({result[0] : [result[1]]})
        else:
            collated_values[result[0]].append(result[1])
    

    for date in collated_values.keys(): # for each day, generate an entry.
        values = collated_values[date]
        print(values)
        entries.append(Entry(site, plot, treatment, "ALL PHOTOS", date,
                             (np.mean(values),
                              np.std(values),
                              np.nanpercentile(values, 50),
                              np.nanpercentile(values, 75),
                              np.nanpercentile(values, 90),
                              np.nanpercentile(values, 95))))
        
    print("processing {}: ...done".format(name))
    return entries

''' this is for old non-super-parallel extraction
if __name__ == "__main__":
    print("GREENNESS: initializing multiprocessing pool (using {} cores)"
          .format(mp.cpu_count()))
    p = mp.Pool(mp.cpu_count())
    percentile = SETTINGS.percentile
    print("{} worker processes started".format(mp.cpu_count()))
    for method, label in SETTINGS.runs:
        masterentries = []
        output_name = label + ".csv"
        methods = [method] * len(cameras)
        percentiles = [percentile] * len(cameras)
        worklist = zip(cameras, cameranames, methods, percentiles)
        results = p.map(process_camera_all_photos, worklist)

        print("writing {}".format(output_name))

        for result in results:
            masterentries.extend(result)

        with open(output_name, mode="w", newline='') as output:
            output_writer = csv.writer(
                output, delimiter=',', quoting=csv.QUOTE_NONE)
            for entry in masterentries:
                output_writer.writerow(entry.return_csv_line())
    p.close()
    p.join()
    print("done")
'''

if __name__ == "__main__":
    print("GREENNESS: initializing multiprocessing pool (using {} cores)"
          .format(mp.cpu_count()))
    p = mp.Pool(mp.cpu_count())
    percentile = SETTINGS.percentile
    print("{} worker processes started".format(mp.cpu_count()))
    for method, label in SETTINGS.runs:
        masterentries = []
        output_name = label + ".csv"
        methods = [method] * len(cameras)
        percentiles = [percentile] * len(cameras)
        worklist = zip(cameras, cameranames, methods, percentiles)
        final_results = []
        for job in worklist:
            final_results.append(process_entire_camera_super_parallel(p, *job))

        print("writing {}".format(output_name))

        for result in final_results:
            masterentries.extend(result)

        with open(output_name, mode="w", newline='') as output:
            output_writer = csv.writer(
                output, delimiter=',', quoting=csv.QUOTE_NONE)
            for entry in masterentries:
                output_writer.writerow(entry.return_csv_line())
    p.close()
    p.join()
    print("done")