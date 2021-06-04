from . import *
import cv2
from PIL import Image
import numpy as np
from math import ceil, sqrt, radians, sin, cos


ALPHA_COLOR = (255, 255, 255, 255)
LINE_TYPE = cv2.LINE_AA


def from_char(c):
    return ''.join(['{:x}'.format(x) for x in c.encode('utf-8')])


def rgb_to_bgr(rgb):
    return rgb[2], rgb[1], rgb[0]


def size_to_html(size, prefix=''):
    return '{}width:{};{}height:{};'\
        .format(prefix,
                str(size[0])+'px' if size[0] >= 0 else '100%',
                prefix,
                str(size[1])+'px' if size[1] >= 0 else '100%')


def rotate_image(iimage, angle, bg_color=(0, 0, 0, 0), padding=False):
    if padding:
        diagonal_length = int(ceil(sqrt(iimage.shape[0] ** 2 + iimage.shape[1] ** 2)))
        image = np.zeros((diagonal_length, diagonal_length, iimage.shape[2]), dtype=np.uint8)

        image_center = (int(image.shape[0] * 0.5), int(image.shape[1] * 0.5))

        ho1, wo1 = int(iimage.shape[0] * 0.5), int(iimage.shape[1] * 0.5)
        ho2, wo2 = iimage.shape[0] - ho1, iimage.shape[1] - wo1

        image[
            image_center[0] - ho1:image_center[0] + ho2,
            image_center[1] - wo1:image_center[1] + wo2
        ] = iimage

    else:
        image = iimage
        image_center = tuple(np.array(image.shape[1::-1]) * 0.5)

    rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)

    bg_color = list(reversed(bg_color[:3])) + list(bg_color[3:])

    result = cv2.warpAffine(image,
                            rot_mat,
                            image.shape[1::-1],
                            flags=cv2.INTER_LINEAR,
                            borderMode=cv2.BORDER_CONSTANT,
                            borderValue=bg_color
                            )
    return result


def overlay_matching(background, foreground):
    fg_image = Image.fromarray(foreground)
    bg_image = Image.fromarray(background)
    bg_image.paste(fg_image, (0, 0), fg_image)
    return np.array(bg_image)


def point_on_circle(angle=0, radius=1, center=(0, 0)):
    angle = radians(int(angle))
    x = center[0] + (radius * cos(angle))
    y = center[1] + (radius * sin(angle))
    return int(x), int(y)


def invert_image(img):
    return 255 - img


def overlay(background, foreground, x=0, y=0, max_size=(-1, -1), align_x='left', align_y='top'):
    if background is None:
        return foreground

    if foreground is None:
        return background

    h, w = foreground.shape[0], foreground.shape[1]

    if align_y == 'bottom':
        n_h = h
        if max_size[1] >= 0:
            n_h = min(max_size[1], h)
        by_start = max(0, y - n_h)
        by_end = min(y, background.shape[0])
        fy_start = h - n_h
        fy_end = by_end
    elif align_y == 'center':
        n_h = h
        if max_size[1] >= 0:
            n_h = min(max_size[1], h)
        hh_a = int(n_h * 0.5)
        hh_b = n_h - hh_a
        by_start = max(0, y - hh_a)
        by_end = min(y + hh_b, background.shape[0])
        fy_start = 0
        fy_end = by_end - by_start
    # Default alignment top
    else:
        if max_size[1] >= 0:
            h = min(max_size[1], h)
        by_start = max(0, y)
        by_end = min(y + h, background.shape[0])
        fy_start = 0
        fy_end = by_end - by_start

    if align_x == 'right':
        n_w = w
        if max_size[0] >= 0:
            n_w = min(max_size[0], w)
        bx_start = max(0, x - n_w)
        bx_end = min(x, background.shape[1])
        fx_start = w - n_w
        fx_end = bx_end

    elif align_x == 'center':
        n_w = w
        if max_size[0] >= 0:
            n_w = min(max_size[0], w)
        hw_a = int(n_w * 0.5)
        hw_b = n_w - hw_a
        bx_start = max(0, x - hw_a)
        bx_end = min(x + hw_b, background.shape[1])
        fx_start = 0
        fx_end = bx_end - bx_start

    # Default alignment left
    else:
        if max_size[0] >= 0:
            w = min(max_size[0], w)
        bx_start = max(0, x)
        bx_end = min(x + w, background.shape[1])
        fx_start = 0
        fx_end = bx_end - bx_start

    if by_end - by_start < 0 or bx_end - bx_start < 0:
        return background

    background = background.copy()

    background[
        by_start:by_end,
        bx_start:bx_end
    ] = overlay_matching(background[by_start:by_end, bx_start:bx_end],
                         foreground[fy_start:fy_end, fx_start:fx_end])

    return background

