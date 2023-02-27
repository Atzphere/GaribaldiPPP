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

'''
REQUIREMENTS
Folder of cameras i.e. the export one produced by avi-rip.py
INVALIDS folder containing copies of invalid images
DUPES folder containing copies of duplicate images
'''

# CONFIGURABLES:

OUTPUT_FILE_NAME = "2022_v2.csv"

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
    def __init__(self, site, plot, treatment, filename,
                 date, greenness_quadrants):
        self.site = site
        self.plot = plot
        self.treatment = treatment
        self.filename = filename
        self.date = date
        self.greenness_quadrants = greenness_quadrants

    def return_csv_line(self):
        return (self.site, self.plot, self.treatment,
                self.filename, self.date, *self.greenness_quadrants)


def get_image_num(imgname, camname):
    return int(imgname.replace(camname + "_day", "").replace(".jpg", ""))


def poster_method_pixelCount(img, minvalue, maxvalue):
    Hue = img[:, :, 0]
    # Make mask of zeroes in which we will set greens to 1
    mask = np.zeros_like(Hue, dtype=np.uint8)

    # Set all green pixels to 1
    mask[(Hue >= minvalue) & (Hue <= maxvalue)] = 1
    return mask.mean() * 100


def get_greenness_quadrants(img, extractor: Callable, itype: str, params=()):
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

    im = np.array(img.convert(itype))
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


def process_camera(zipped):
    '''
    Wrapper for processing a tuple of (camera, cameraname)
    for multiprocessing.

    Returns a list of Entry objects.
    '''
    camera, name = zipped
    entries = []
    processed_already = []
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
                entries.append(
                    Entry(site, plot, treatment, img, date,
                          get_greenness_quadrants(img_data,
                                                  poster_method_pixelCount,
                                                  "HSV", (80, 90))))
                date += dt.timedelta(days=1)
                processed_already.append(imgname)
    return entries


if __name__ == "__main__":
    masterentries = []
    print("GREENNESS: initializing multiprocessing pool (using {} cores)"
          .format(mp.cpu_count()))
    p = mp.Pool(mp.cpu_count())
    print("{} worker processes started".format(mp.cpu_count()))
    data = zip(cameras, cameranames)
    results = p.map(process_camera, data)
    for result in results:
        masterentries.extend(result)

    with open(OUTPUT_FILE_NAME, mode="w", newline='') as output:
        output_writer = csv.writer(
            output, delimiter=',', quoting=csv.QUOTE_NONE)
        for entry in masterentries:
            output_writer.writerow(entry.return_csv_line())
    p.close()
    p.join()
    print("done")
