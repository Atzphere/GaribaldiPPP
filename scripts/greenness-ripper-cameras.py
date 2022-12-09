'''
Generates average greenness over time plots for each community/warming type
Somewhat deprecated by master-greenness.py - ideally you should just run that
to generate the entire dataset and do what you need from there.

Code here runs much slower and the greenness algorithm may be different
but I'll leave this here for future reference.
'''
import numpy as np
import numpy_indexed as npi
import _datetime as dt
import dirtools
from PIL import Image
import itertools


CASS_START = dt.date.fromisoformat("2022-07-21")
SAL_START = dt.date.fromisoformat("2022-07-21")
MEAD_START = dt.date.fromisoformat("2022-08-06")

nan = np.nan

cameras = dirtools.get_subdirs("./greeness-data", fullpath=True)
cameranames = dirtools.get_subdirs("./greeness-data")
INVALIDS = dirtools.get_files("./INVALIDS")
DUPES = dirtools.get_files("./DUPES")

INVALIDS_WL = dirtools.get_files("./INVALIDS", fullpath=True)
DUPES_WL = dirtools.get_files("./DUPES", fullpath=True)


def get_image_num(imgname, camname):
    return int(imgname.replace(camname + "_day", "").replace(".jpg", ""))


def get_greenness(img):
    '''
    From Mark Setchell's response to this StackOverflow post:
    https://stackoverflow.com/questions/56569418/estimating-the-percentage-of-green-in-an-image

    Modified with a greater greeness range and saturation filtering.

    '''
    minvalue = 80
    maxvalue = 90
    # Load image and convert to HSV
    im = Image.open(img).convert('HSV')

    # Extract Hue channel and make Numpy array for fast processing
    Hue = np.array(im.getchannel('H'))
    Sat = np.array(im.getchannel('S'))
    # Make mask of zeroes in which we will set greens to 1
    mask = np.zeros_like(Hue, dtype=np.uint8)

    # Set all green pixels to 1
    mask[(Hue >= minvalue) & (Hue <= maxvalue)] = 1

    # Now print percentage of green pixels
    return mask.mean() * 100


greenness = get_greenness

MEAD_C_averages = []
CASS_C_averages = []
SAL_C_averages = []

MEAD_W_averages = []
CASS_W_averages = []
SAL_W_averages = []

for camera, name in zip(cameras, cameranames):
    image_names = dirtools.get_files(camera)
    image_names.extend([i for i in INVALIDS if name in i])
    image_names.extend([i for i in DUPES if name in i])

    image_wl = dirtools.get_files(camera, fullpath=True)
    image_wl.extend([i for i in INVALIDS_WL if name in i])
    image_wl.extend([i for i in DUPES_WL if name in i])

    image_nums = [get_image_num(i, name) for i in image_names]
    image_names = [x for _, x in sorted(zip(image_nums, image_names))]
    image_wl = [x for _, x in sorted(zip(image_nums, image_wl))]

    if "CASS" in name:
        start = CASS_START
        output = CASS_C_averages
        if "W" in name:
            output = CASS_W_averages
    elif "MEAD" in name:
        start = MEAD_START
        output = MEAD_C_averages
        if "W" in name:
            output = MEAD_W_averages
    elif "SAL" in name:
        start = SAL_START
        output = SAL_C_averages
        if "W" in name:
            output = SAL_W_averages
    print("processing {}".format(name))
    date = start
    rsf = []
    time = []
    plots = []
    pnums = []
    for img, imgname in zip(image_wl, image_names):
        if imgname in INVALIDS:
            rsf.append(nan)
            time.append(date)

            date += dt.timedelta(days=1)
        elif imgname in DUPES:
            pass
        else:
            rsf.append(greenness(img))
            time.append(date)
            date += dt.timedelta(days=1)
    output.append([time, rsf])

for data, com in zip((CASS_C_averages, MEAD_C_averages, SAL_C_averages,
                      CASS_W_averages, MEAD_W_averages, SAL_W_averages),
                     ("CASS_C_m1", "MEAD_C_m1", "SAL_C_m1", "CASS_W_m1", "MEAD_W_m1", "SAL_W_m1")):
    x = np.array(list(itertools.chain(
        *list([pair[0] for pair in data])))).astype(dt.datetime)
    y = np.array(list(itertools.chain(*list([pair[1] for pair in data]))))
    x_unique, y_mean = npi.group_by(x).mean(y)
    np.savetxt(
        com + ".csv", np.transpose([x_unique, y_mean]), delimiter=",", fmt='%s')

# [[[a b],[1 2]]]
