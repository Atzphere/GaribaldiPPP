import numpy as np
import datetime as dt
import cv2
from matplotlib import pyplot as plt
import dirtools
import os
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

project_home = dirtools.get_parent_dir(os.getcwd(), depth=2)
test_files = project_home+"/testing/"
os.chdir(project_home)
workingdir = os.getcwd()

print(project_home)
class Camera:
    class Image:
        '''
        Wrapper class to associate an apeman image file with metadata as well as useful functions.
        '''
        def __init__(self, path, metadata={}):
            '''
            path of image file and associated metadata
            '''
            self.path = path
            self.metadata = metadata
            self.image_loaded = False

        def load_image(self):
            self.loaded_image = cv2.imread(self.path)
            self.image_loaded = True

        def get_date_created(self):
            def get_date_region():
                y1, y2 = 3742, 3890
                x1, x2 = 4100, 4980
                if not self.image_loaded:
                    self.load_image()
                return self.loaded_image[y1:y2, x1:x2, :]

            date_region = get_date_region()
            plt.imshow(get_date_region())
            plt.show()
            blur = cv2.GaussianBlur(date_region, (3,3), 0)
            date_str = pytesseract.image_to_string(blur, lang='eng', config='--psm 8')
            print(date_str)
            
                
    def __init__(self, folder_path):
        self.folder_path = folder_path

source = "C:\\Users\\allen\\Documents\\Garibaldi ITEX\\testing\\"
files = [os.path.join(source, f) for f in os.listdir(
        source) if os.path.isfile(os.path.join(source, f))]

print(files)
for f in files:
    foo = Camera.Image(f)
    foo.get_date_created()
