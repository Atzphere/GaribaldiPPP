import cv2
from PIL import Image, ImageFont, ImageDraw
from skimage import io
import dirtools as dt
import numpy as np
import whitebalance
import matplotlib
from matplotlib import pyplot as plt
scale = 3.0
IMAGE_WIDTH = int(160 * scale)
IMAGE_HEIGHT = int(90 * scale)
# matplotlib.use('GTK3Agg')

def get_timestamp(imgname):
    return imgname[len(imgname) - 12: len(imgname) - 4]


source_imgs = []
exp_folder = "/home/azhao/projects/def-nbl/Garibaldi_Lake_shared/working_directories/azhao_pheno_processing_workingdir/GaribaldiPPP/scripts/collage/"
data_folder = "/home/azhao/projects/def-nbl/Garibaldi_Lake_shared/working_directories/azhao_pheno_processing_workingdir/export_all_photos_v3/MEAD_19C"
days = dt.get_subdirs(data_folder, fullpath=True)

for day in days:
    image_wl = dt.get_files(day, fullpath=True)
    image_names = dt.get_files(day, fullpath=False)
    for img, imgname in zip(image_wl, image_names):
        # print(day)
        ref = img
        if get_timestamp(imgname) == "12:00:00":
            # print("reference image found.")
            break
    source_imgs.append(ref)


# filler = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT))
# cv2.cvtColor(np.array(filler), cv2.COLOR_RGB2BGR)
filler = np.zeros((IMAGE_HEIGHT, IMAGE_WIDTH))


def get_rgb(img):
    return np.mean(img[:, :, 0]), np.mean(
        img[:, :, 1]), np.mean(img[:, :, 2])


def create_collage(images):
    # io.imread(img)
    images = [cv2.cvtColor(cv2.imread(img), cv2.COLOR_BGR2RGB) for img in images]
    for n, image in enumerate(images):
        images[n] = 255 - image
    plt.imshow(images[0])
    plt.show()
    images = [cv2.resize(image, (IMAGE_WIDTH, IMAGE_HEIGHT)) * 255
              for image in images]
    #images = [whitebalance.percentile_white_balance(cv2.resize(image, (IMAGE_WIDTH, IMAGE_HEIGHT)), 90) * 255
    #          for image in images]
    print(len(images))
    for image in images:
        image = cv2.putText(img=image, text="{:.2f}, {:.2f}, {:.2f}".format(*get_rgb(image)), org=(IMAGE_WIDTH // 3, IMAGE_HEIGHT // 2),
                            fontFace=3, fontScale=1, color=(255, 0, 0), thickness=5)

    h = w = int(np.ceil(np.sqrt(len(images))))
    canvas = Image.new("RGBA", (IMAGE_WIDTH * h, IMAGE_HEIGHT * w))
    for i in range(0, h):
        for i2 in range(0, w):
            if len(images) > 0:
                im = images.pop(0)
                if np.mean(im) < 1.1:
                    im = np.uint8(im * 255)
                    print("converted")
                else:
                    print(np.mean(im))

                print("pasted")
                canvas.paste(Image.fromarray(im, "RGB"), (i2 * IMAGE_WIDTH, i * IMAGE_HEIGHT))
            else:
                break

    image_name = "result.jpg"
    image = canvas.convert("RGB")
    image.save(exp_folder + image_name)

create_collage(source_imgs)