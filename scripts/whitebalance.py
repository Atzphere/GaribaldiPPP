import numpy as np
from PIL import Image
# import cv2

def percentile_white_balance(img, percentile=100):
    """White balance an image based on percentile values.

    Args:
        img (np.arrar): Image to be white balanced.
        percentile (float): Percentile value to use.
    """
    patch = np.percentile(img, percentile, axis=(0, 1))
    white_patch_image = (img * 1.0 / patch)
    return white_patch_image


def patch_white_balance(img, from_row, from_column, row_width, column_width):
    """White balance an image based on a white patch location.
    """
    image_patch = img[from_row:from_row + row_width,
                      from_column:from_column + column_width]
    image_max = (img * 1.0 / image_patch.max(axis=(0, 1)))
    return image_max


def srgb_to_rgb(srgb):
    ret = np.zeros_like(srgb)
    idx0 = srgb <= 0.04045
    idx1 = srgb > 0.04045
    ret[idx0] = srgb[idx0] / 12.92
    ret[idx1] = np.power((srgb[idx1] + 0.055) / 1.055, 2.4)
    return ret


def rgb_to_srgb(rgb):
    ret = np.zeros_like(rgb)
    idx0 = rgb <= 0.0031308
    idx1 = rgb > 0.0031308
    ret[idx0] = rgb[idx0] * 12.92
    ret[idx1] = np.power(1.055 * rgb[idx1], 1.0 / 2.4) - 0.055
    return ret

'''
def load_image(fname):
    img = cv2.imread(fname)
    img_arr = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_lin = srgb_to_rgb(img_arr)
    img_wb = percentile_white_balance(img_lin, percentile=95)
    img_arr = rgb_to_srgb(img_lin)
    return img_arr
'''