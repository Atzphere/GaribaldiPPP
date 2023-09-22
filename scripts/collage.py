import cv2
from PIL import Image, ImageFont, ImageDraw
from skimage import io
import dirtools as dt
import numpy as np
import whitebalance

IMAGE_WIDTH = 102
IMAGE_HEIGHT = 57

def get_timestamp(imgname):
    return imgname[len(imgname) - 12: len(imgname) - 4]
images = []
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


filler = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT))

images = ["image1.png", "image2.png", "image3.png", "image4.png"]


def get_rgb(img):
    return np.mean(img[:, :, 0]), np.mean(
        img[:, :, 1]), np.mean(img[:, :, 2])


def create_collage(images):
    images = [io.imread(img) for img in images]
    images = [whitebalance.percentile_white_balance(cv2.resize(image, (IMAGE_WIDTH, IMAGE_HEIGHT)), 90) * 255
              for image in images]
    for image in images:
        image = cv2.putText(img=image, text="{}, {}, {}".format(str(get_rgb(image))), org=(IMAGE_WIDTH // 2, IMAGE_HEIGHT // 2),
                            fontFace=3, fontScale=3, color=(255, 0, 0), thickness=5)
    h = w = np.ceil(len(images))
    while len(images) < h * w:
        images.append(filler)
    verts = []
    for i in range(0, h):
        horos = []
        for i in range(0, w):
            if len(images > 0):
                horos.append(images.pop())
        verts.append(cv2.hconcat(horos))
    concat_images = cv2.vconcat(verts)
    image = Image.fromarray(concat_images)

    # Image path
    image_name = "result.jpg"
    image = image.convert("RGB")
    image.save(f"{image_name}")
    return image_name


# image1 on top left, image2 on top right, image3 on bottom left,image4 on bottom right
create_collage(images)
