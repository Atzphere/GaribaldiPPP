'''
Module for all things apeman camera after processing via avi-rip.py
I've tried to wrap all the associated information in as neat of a thing
as possible using classes.

This module is NOT for specific image content stuff like greenness index,
ONLY metadata.

Not completely done yet but the planned
main gist of it goes like the following:

Camera class: contains an entire camera's worth of Image data from one season

Image class: wrapper for every individual image to store metadata.

Classes:

    Camera
        Image

'''

import numpy as np
import _datetime as dt
import cv2
import dirtools
import os
import pytesseract

# pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"


# project_home = dirtools.get_parent_dir(os.getcwd(), depth=2)
# os.chdir(project_home)


class Image:
    '''
    Wrapper class to associate an apeman image file with metadata as well as useful functions.

    ...

    Attributes:
    -----------
    Global constants:

    errorDateErrorImage : np.ndarray, constant
        error code array for when an invalid image is processed
    errorDateErrorImage : datetime.date, constant
        error code date for when an invalid image is detected.
    errorDateOCRFailed : datetime.date, constant
        returned when pytesseract OCR fails to return a valid date string
        this is likely to be caused by image corruption.
    errorTempOCRFailed : int
        error code when an invalid temperature is obtained from OCR.


    Instance attributes:

    path : os.path (str)
        the filepath for the image
    metadata : dict
        any metadata tags associated with the image i.e. data.
    image_loaded : bool
        whather or not the actual image file has been loaded 
        into self.loaded_image.
    self.loaded_image : np.ndarray (shape (x, y, 3))
        loaded image file in the form of a numpy ndarray.
    self.is_error_image : boolean
        whether or not the image object represents an error image.

    Methods
    -------
    load_image():
        Loads the image from self.path
    get_date_created():
        Uses OCR to read the data part of Apeman images
    get_temperature():
        Inconsistent (feel free to try and improve).
        Uses OCR to read the temperature part of Apeman images
    '''
    errorCodeInvalidImage = np.zeros((3, 5))
    errorDateErrorImage = dt.date(1, 1, 1)
    errorDateOCRFailed = dt.date(2, 1, 1)
    errorTempErrorImage = -500
    errorTempOCRFailed = -250

    def __init__(self, path, metadata={}):
        '''
        path of image file and associated metadata
        '''
        self.path = path
        self.metadata = metadata
        self.image_loaded = False
        self.is_error_image = False
        self.metadata_executables = {"date": self.get_date_created,
                            "temperature" : self.get_temperature}

    def load_image(self):
        if not self.image_loaded:
            self.loaded_image = cv2.imread(self.path)
            self.image_loaded = True
            if np.shape(self.loaded_image) == (300, 300, 3):
                self.is_error_image = True

    def get_date_created(self):
        def get_date_region():
            y1, y2 = 3742, 3890
            x1, x2 = 4100, 4980
            self.load_image()
            if self.is_error_image:
                print("{path} is not a valid image (most likely an error image)"
                      .format(path=self.path))
                return self.errorCodeInvalidImage
            return self.loaded_image[y1:y2, x1:x2, :]

        date_region = get_date_region()
        if np.array_equal(date_region, self.errorCodeInvalidImage):
            print("Aborting date extraction... (returning default date)")
            return self.errorDateErrorImage

        # plt.imshow(get_date_region())
        # plt.show()
        img = cv2.resize(date_region, None, fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC)
        kernel = np.ones((1, 1), np.uint8)
        img = cv2.dilate(img, kernel, iterations=1)
        img = cv2.erode(img, kernel, iterations=1)
        blur = cv2.GaussianBlur(img, (3, 3), 0)
        date_str = pytesseract.image_to_string(
            blur, lang='eng', config='--psm 8')
        date_str = date_str.replace("/", "-").strip()
        try:
            return dt.date.fromisoformat(date_str)
        except ValueError:
            print("possible date OCR failure: {p}"
                  .format(p=self.path))
            return self.errorDateOCRFailed

    def get_temperature(self):
        def get_temp_region():
            y1, y2 = 3742, 3890
            x1, x2 = 1500 + 150, 1865
            self.load_image()
            if self.is_error_image:
                print("{path} is not a valid image (most likely an error image)"
                      .format(path=self.path))
                return self.errorCodeInvalidImage
            return ~self.loaded_image[y1:y2, x1:x2, :]
        # plt.imshow(get_temp_region())
        # plt.show()
        temp_region = get_temp_region()
        if np.array_equal(temp_region, self.errorCodeInvalidImage):
            print("Aborting temperature extraction... (returning default temperature)")
            return self.errorTempErrorImage

        # blur = cv2.GaussianBlur(temp_region, (3,3), 0)
        blur = temp_region
        temp_str = pytesseract.image_to_string(
            blur, lang='eng', config='--psm 6 -c tessedit_char_whitelist=0123456789')
        try:
            return int(temp_str.strip())
        except:
            print("possible temperature OCR failure: {p}"
                  .format(p=self.path))
            print(temp_str)
            return self.errorTempOCRFailed



class Camera:
    '''
    Class representing an Apeman camera and its image data.

    ...

    Attributes
    ----------
    folder_path : os.path (str)
        file path of the camera's image library (AFTER AVI EXTRACTION)


    '''

    def __init__(self, folder_path, images=[]):
        self.folder_path = folder_path
        self.images = images

    def build_camera_database(self, extract=["get_date_created"]):
        '''
        Generates a list of Image objects - one for every image found in
        the camera's image library combined with its metadata if desired.
        '''
        def process_image(path):
            '''
            wrapper for Pool.map() for stuff to do to images
            '''
            img = Image(path)
            for md in extract:
                img.metadata.update({md: getattr(img, md)()})
            return img

        image_dirs = dirtools.get_files(self.folder_path, fullpath=True)
        self.images = map(process_image, image_dirs)
        return self.images





if __name__ == "__main__":  # testing stuff for OCR accuracy
    from matplotlib import pyplot as plt
    '''
    source = "C:\\Users\\allen\\Documents\\Garibaldi ITEX\\testing\\"
    files = dirtools.get_files(source, fullpath=True)

    benchmark = [24, -500, 15, 20, 22, 22, 21, 24, 23, 17, 19, 14, 20, 20, 25,
                 25, 15, 11, 16, 22, 25, 26, 23, 25, 20, 10, 8, 13, 16, 13, 15, 15, 13, 19]
    failures = 0
    for i, j in zip(files, benchmark):
        img = Image(i)
        guess = img.get_temperature()
        print(guess == j)
        if guess != j:
            print("OCR Failure: with expected value: {val}, OCR value: {ocr}"
                  .format(val=j, ocr=guess))
            failures += 1
    print("total failure rate: {}%".format((100 * failures / len(files))))
    '''
    foo = Camera("/home/azhao/projects/def-henryg/Garibaldi_Lake_data_summer2022/azhao_pheno_processing_workingdir/export/MEAD_20W")
    foo.build_camera_database()
    for i in foo.images:
        print(i.metadata["get_date_created"])
        #plt.imshow(i.loaded_image)
        #plt.show()
