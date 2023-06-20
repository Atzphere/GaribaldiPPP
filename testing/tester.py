import PIL
from PIL import Image
from matplotlib import pyplot as plt
import numpy as np
from skimage import color
from skimage import io
import dirtools as dt
from wbtest import percentile_white_balance

def percentile_white_balance(img, percentile=100):
    """White balance an image based on percentile values.

    Args:
        img (np.arrar): Image to be white balanced.
        percentile (float): Percentile value to use.
    """
    patch = np.percentile(img, percentile, axis=(0, 1))
    white_patch_image = (img * 1.0 / patch)
    return white_patch_image


def load_image(path):
    return Image.open(path)


def GCC(im):
    img = np.array(im)
    red, green, blue = np.mean(img[:, :, 0]), np.mean(
        img[:, :, 1]), np.mean(img[:, :, 2])
    return (green / (red + green + blue))


def dark_pixel_norm(img):
    pass


def monotone(img):
    return color.rgb2gray(img)


'''
plt.imshow(monotone(load_image("CASS_10W_day050_013_.jpg")),
           cmap='gray', vmin=0, vmax=1)
foo = np.array(monotone(load_image("CASS_10W_day050_013_.jpg")))[
               :, :3620] * 255
print(foo)
print(np.shape(foo))
print(np.min(foo))
plt.show()
foo[foo == np.min(foo)]
'''
images = dt.get_files("./data/", fullpath=True)
width = height = int(np.ceil(np.sqrt(len(images))))

fig, ax = plt.subplots(width, height)
cnt = 0

for i in range(0, height):
    for j in range(width):
        if cnt < len(images):
            im = load_image(images[cnt])
            # wbalanced = percentile_white_balance(np.array(im), 90)
            ax[i, j].imshow(im)
            ax[i, j].axis("off")
            ax[i, j].text(*tuple(np.array(np.shape(im)[0:2]) // 2), GCC(im), c="white")
            cnt += 1
        else:
            break

plt.show()
