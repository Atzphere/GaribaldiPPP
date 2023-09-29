import cv2
from PIL import Image, ImageFont, ImageDraw
from skimage import io
import dirtools as dt
import numpy as np
import whitebalance
scale = 3.0
IMAGE_WIDTH = int(160 * scale)
IMAGE_HEIGHT = int(90 * scale)

def get_timestamp(imgname):
    return imgname[len(imgname) - 12: len(imgname) - 4]
images = []
exp_folder = "/home/azhao/projects/def-nbl/Garibaldi_Lake_shared/working_directories/azhao_pheno_processing_workingdir/GaribaldiPPP/scripts/collage/"
data_folder = "/home/azhao/projects/def-nbl/Garibaldi_Lake_shared/working_directories/azhao_pheno_processing_workingdir/export_all_photos_v3/MEAD_19C"
days = dt.get_subdirs(data_folder, fullpath=True)
    
for day in days:
    image_wl = dt.get_files(day, fullpath=True)
    image_names = dt.get_files(day, fullpath=False)
    for img, imgname in zip(image_wl, image_names):
        ref = img
        if get_timestamp(imgname) == "12:00:00":
            # print("reference image found.")
            break
    images.append(ref)


# filler = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT))
filler = np.zeroes((IMAGE_HEIGHT, IMAGE_WIDTH))# cv2.cvtColor(np.array(filler), cv2.COLOR_RGB2BGR)

def get_rgb(img):
    return np.mean(img[:, :, 0]), np.mean(
        img[:, :, 1]), np.mean(img[:, :, 2])

def create_collage(images):
    # io.imread(img)
    images = [cv2.imread(img) for img in images]
    images = [whitebalance.percentile_white_balance(cv2.resize(image, (IMAGE_WIDTH, IMAGE_HEIGHT)), 90) * 255
              for image in images]
    for image in images:
        image = cv2.putText(img=image, text="{}, {}, {}".format(*get_rgb(image)), org=(IMAGE_WIDTH // 2, IMAGE_HEIGHT // 2),
                            fontFace=3, fontScale=3, color=(255, 0, 0), thickness=5)
    h = w = int(np.ceil(np.sqrt(len(images))))
    while len(images) < h * w:
        images.append(filler)
    print("square?", len(images))
    verts = []
    for i in range(0, h):
        horos = []
        for i in range(0, w):
            if len(images) > 0:
                horos.append(images.pop(0))
        verts.append(cv2.hconcat(horos))
    prev = np.shape(verts[0])
    for n, v in enumerate(verts):
        print(np.shape(v))
        image_name = "result{}.jpg".format(n)
        image = Image.fromarray((image * 255).astype(np.uint8))
        image = image.convert("RGB")
        image.save(exp_folder + image_name)
        return image_name
'''
    for v in verts:
        print(np.shape(v))
        print(type(v))
        if np.shape(v) != prev:
            print("failure")
            assert False    
        else:
            prev = np.shape(v)
    concat_images = cv2.vconcat(verts)
    image = Image.fromarray(concat_images)
'''
'''
    # Image path
    image_name = "result.jpg"
    image = image.convert("RGB")
    image.save(f"{image_name}")
    return image_name
    '''


# image1 on top left, image2 on top right, image3 on bottom left,image4 on bottom right
create_collage(images)
