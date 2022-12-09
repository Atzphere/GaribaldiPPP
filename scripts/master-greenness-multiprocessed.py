import numpy as np
import _datetime as dt
import dirtools
from PIL import Image
import csv
import multiprocess as mp

'''
REQUIREMENTS
Folder of cameras i.e. the ones produced by avi-rip.py
INVALIDS folder - 
'''

OUTPUT_FILE_NAME = "2022.csv"

CASS_START = dt.date.fromisoformat("2022-07-21")
SAL_START = dt.date.fromisoformat("2022-07-21")
MEAD_START = dt.date.fromisoformat("2022-08-06")

# determines what settings to apply depending on the community type:
# here the first setting is the community name and the second is the start date
# for camera recording for that community
COMMUNITY_SETTINGS = {"CASS": ("CASS", CASS_START),
                      "MEAD": ("MEAD", MEAD_START),
                      "SAL": ("SAL", SAL_START)}

nan = np.nan

null_quads = (nan, nan, nan, nan)

cameras = dirtools.get_subdirs("./greeness-data", fullpath=True)
cameranames = dirtools.get_subdirs("./greeness-data")
INVALIDS = dirtools.get_files("./INVALIDS")
DUPES = dirtools.get_files("./DUPES")

INVALIDS_WL = dirtools.get_files("./INVALIDS", fullpath=True)
DUPES_WL = dirtools.get_files("./DUPES", fullpath=True)


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


def get_greenness_quadrants(img):
    minvalue = int(80)
    maxvalue = int(90)
    im = np.array(img)
    M = im.shape[0] // 2
    N = im.shape[1] // 2
    quadrants = [im[x:x + M, y:y + N]
                 for x in range(0, im.shape[0], M)
                 for y in range(0, im.shape[1], N)]

    quad_greenness = []

    for quadrant in quadrants:
        Hue = quadrant[:, :, 0]
        # Make mask of zeroes in which we will set greens to 1
        mask = np.zeros_like(Hue, dtype=np.uint8)

        # Set all green pixels to 1
        mask[(Hue >= minvalue) & (Hue <= maxvalue)] = 1
        quad_greenness.append(mask.mean() * 100)

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
    image_names = dirtools.get_files(camera)
    image_names.extend([i for i in INVALIDS if name in i])
    image_names.extend([i for i in DUPES if name in i])

    image_wl = dirtools.get_files(camera, fullpath=True)
    image_wl.extend([i for i in INVALIDS_WL if name in i])
    image_wl.extend([i for i in DUPES_WL if name in i])

    image_nums = [get_image_num(i, name) for i in image_names]
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
                img_data = Image.open(img).convert('HSV')
                entries.append(Entry(site, plot, treatment, img, date,
                                     get_greenness_quadrants(img_data)))
                date += dt.timedelta(days=1)
                processed_already.append(imgname)
    return entries


if __name__ == "__main__":
    masterentries = []
    p = mp.Pool(mp.cpu_count())
    data = zip(cameras, cameranames)
    results = p.map(process_camera, data)
    for result in results:
        masterentries.extend(result)

    with open(OUTPUT_FILE_NAME, mode="w", newline='') as output:
        output_writer = csv.writer(
            output, delimiter=',', quoting=csv.QUOTE_NONE)
        for entry in masterentries:
            output_writer.writerow(entry.return_csv_line())
    print("done")
