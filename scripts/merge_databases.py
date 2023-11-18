'''
Script for merging two day-segmented processed images from avi-rip-all
in the event of two separate data uploads throughout the season.

Given a primary directory of day000, day001... folders to merge into,
the script will automatically find the last day and append the secondary
folder starting from the following day, theoretically preserving
time canonicity.
'''
import dirtools as dt
import os
from tqdm import tqdm
import pathlib
import shutil

PRIMARY_DIR = "/home/azhao/projects/def-nbl/Garibaldi_Lake_shared/working_directories/azhao_pheno_processing_workingdir/2023_processed_photos/export_all_photos/"
SECONDARY_DIR = "/home/azhao/projects/def-nbl/Garibaldi_Lake_shared/working_directories/azhao_pheno_processing_workingdir/2023_processed_photos/export_all_photos_sept/"

def get_day_num(dirname):
    daypos = dirname.index("day")
    return int(dirname[daypos + 3: daypos + 6])

def reassign_image_date(imgname, newnum):
    s1, s2, s3 = imgname.partition("day")
    return s1 + s2 + f"{newnum:03}" + s3[3:]

inc = "Target and source folders are not compatible. Make sure naming is consistent."

print("""Current merge operation:
    {}
    |||
    VVV
    {}"""
      .format(SECONDARY_DIR, PRIMARY_DIR))

choice = input("Would you like to continue with this (y/n)")
if choice == "y":
    tf = dt.get_subdirs(PRIMARY_DIR, fullpath=True)
    sf = dt.get_subdirs(SECONDARY_DIR, fullpath=True)
    tfn = [os.path.basename(x) for x in tf]
    sfn = [os.path.basename(x) for x in sf]
    tf = [x for _, x in sorted(zip(tfn, tf))]  # assuming canonical sorting...
    sf = [x for _, x in sorted(zip(sfn, sf))]
    tfn.sort()
    sfn.sort()

    assert all([x == y for x, y
                in zip(tfn, sfn)]), inc
    print("Source and destination folders are compatible; proceeding...")
    for target_cam, source_cam in zip(tf, sf):
        target_days = dt.get_subdirs(target_cam)
        source_days = dt.get_subdirs(source_cam, fullpath=True)
        print("\nConsolidating {}:".format(os.path.basename(target_cam)))
        ltd = get_day_num(target_days[-1])  # last target day
        print("Starting merge from day {}".format(ltd))
        for day in tqdm(source_days, desc=os.path.basename(target_cam)):
            ltd += 1
            newday_path = PRIMARY_DIR+f'day{ltd:03}/'
            pathlib.Path(newday_path).mkdir(parents=True, exist_ok=True)
            for file in dt.get_files(day, fullpath=True):
                shutil.copyfile(file, newday_path + reassign_image_date(os.path.basename(file), ltd))




else:
    print("quitting...")
    quit()
