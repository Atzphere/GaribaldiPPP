import cv2
from PIL import Image, ImageFont, ImageDraw
# from skimage import io
import dirtools as dt
import numpy as np
import whitebalance
import matplotlib
# matplotlib.use('tkagg')
from matplotlib import pyplot as plt
from tqdm import tqdm
import os

scale = 3.0
IMAGE_WIDTH = int(160 * scale)
IMAGE_HEIGHT = int(90 * scale)

cam_folder = dt.get_subdirs("/home/azhao/projects/def-nbl/Garibaldi_Lake_shared/working_directories/azhao_pheno_processing_workingdir/2022_processed_photos/export_all_photos", fullpath=True)
exp_folder = "/home/azhao/projects/def-nbl/Garibaldi_Lake_shared/working_directories/azhao_pheno_processing_workingdir/GaribaldiPPP/scripts/collage_2023/"

def get_timestamp(imgname):
    return imgname[len(imgname) - 12: len(imgname) - 4]



# filler = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT))
# cv2.cvtColor(np.array(filler), cv2.COLOR_RGB2BGR)
filler = np.zeros((IMAGE_HEIGHT, IMAGE_WIDTH))

def get_ccc(img):
    red, green, blue = np.mean(img[:, :, 0]), np.mean(
    img[:, :, 1]), np.mean(img[:, :, 2])
    return (red / (red + green + blue), green / (red + green + blue), blue / (red + green + blue))

def get_rgb(img):
    return np.mean(img[:, :, 0]), np.mean(
        img[:, :, 1]), np.mean(img[:, :, 2])


def create_collage(images):
    # io.imread(img)
    images = [cv2.cvtColor(cv2.imread(img), cv2.COLOR_BGR2RGB)
              for img in tqdm(images, desc="color space trans. pt.1")]
    for n, image in tqdm(enumerate(images), desc="color space trans. pt.2"):
        images[n] = 255 - image
    #plt.imshow(images[0])
    #plt.show()
    images = [cv2.resize(image, (IMAGE_WIDTH, IMAGE_HEIGHT)) * 255
              for image in tqdm(images, desc="resize")]
    #images = [whitebalance.percentile_white_balance((cv2.resize(image, (IMAGE_WIDTH, IMAGE_HEIGHT))), 70)
    #          for image in images]
    for n, image in tqdm(enumerate(images), desc="apply image labels"):
        image = cv2.putText(img=image, text="day {}\n{:.2f}, {:.2f}, {:.2f}".format(n, *get_ccc(image)), org=(IMAGE_WIDTH // 6, IMAGE_HEIGHT // 2),
                            fontFace=3, fontScale=1, color=(255, 0, 0), thickness=3)
        pass
    h = w = int(np.ceil(np.sqrt(len(images))))
    canvas = Image.new("RGBA", (IMAGE_WIDTH * h, IMAGE_HEIGHT * w))
    for i in tqdm(range(0, h), desc="pasting canvas"):
        for i2 in range(0, w):
            if len(images) > 0:
                im = images.pop(0)
                if np.mean(im) < 1.1:
                    im = np.uint8(im * 255)
                    print("converted")
                else:
                    print(np.mean(im))

                canvas.paste(Image.fromarray(im, "RGB"),
                             (i2 * IMAGE_WIDTH, i * IMAGE_HEIGHT))
            else:
                break

    image_name = "result_{}.jpg".format(data_folder[145:])
    image = canvas.convert("RGB")
    print("saving...")
    image.save(exp_folder + image_name)
    del canvas

for data_folder in cam_folder:
    # print(data_folder[145:])
    source_imgs = []
    # data_folder = "/home/azhao/projects/def-nbl/Garibaldi_Lake_shared/working_directories/azhao_pheno_processing_workingdir/2022_processed_photos/export_all_photos_v3/MEAD_19C"
    nums = [int(x[-3:]) for x in dt.get_subdirs(data_folder, fullpath=True)]
    days = [x for _, x in sorted(zip(nums, dt.get_subdirs(data_folder, fullpath=True)))]
    # print([int(x[-3:]) for x in days])

    for day in tqdm(days, desc=os.path.basename(data_folder)):
        image_wl = dt.get_files(day, fullpath=True)
        image_names = dt.get_files(day, fullpath=False)
        for img, imgname in zip(image_wl, image_names):
            # print(day)
            ref = img
            if get_timestamp(imgname) == "12:00:00":
                # print("reference image found.")
                break

        source_imgs.append(ref)
    print(f"...done {os.path.basename(data_folder)}, building collage")

    create_collage(source_imgs)
