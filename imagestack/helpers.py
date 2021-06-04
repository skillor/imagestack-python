from . import *
import cv2
from PIL import Image
import numpy as np
from math import ceil, sqrt, radians, sin, cos
import re


ALPHA_COLOR = (255, 255, 255, 255)
LINE_TYPE = cv2.LINE_AA


def from_char(c):
    return ''.join(['{:x}'.format(x) for x in c.encode('utf-8')])


def rgb_to_bgr(rgb):
    return rgb[2], rgb[1], rgb[0]


def html_relative_position_x(width, align_x):
    rel_x = 0
    if width >= 0:
        if align_x == 'center':
            rel_x -= int(width / 2)
        elif align_x == 'right':
            rel_x -= width
    return rel_x


def html_relative_position_y(height, align_y):
    rel_y = 0
    if height >= 0:
        if align_y == 'center':
            rel_y -= int(height / 2)
        elif align_y == 'bottom':
            rel_y -= height
    return rel_y


def html_relative_position(size, align_x, align_y):
    return html_relative_position_x(size[0], align_x), html_relative_position_y(size[1], align_y)


def size_to_html(size, el, prefix='', relative=False):
    width = '100%'
    if size[0] >= 0:
        if relative:
            width = str(size[0] + html_relative_position_x(size[0], el.align_x)) + 'px'
        else:
            width = str(size[0]) + 'px'
    height = '100%'
    if size[1] >= 0:
        if relative:
            height = str(size[1] + html_relative_position_y(size[1], el.align_y)) + 'px'
        else:
            height = str(size[1]) + 'px'
    return '{}width:{};{}height:{};'\
        .format(prefix, width, prefix, height)


def is_emoji(emoji):
    if len(emoji) != 1:
        return False
    regex_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"
                               u"\U0001F300-\U0001F5FF"
                               u"\U0001F680-\U0001F6FF"
                               u"\U0001F1E0-\U0001F1FF"
                               u"\U00002500-\U00002BEF"
                               u"\U00002702-\U000027B0"
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               u"\U0001f926-\U0001f937"
                               u"\U00010000-\U0010ffff"
                               u"\u2640-\u2642"
                               u"\u2600-\u2B55"
                               u"\u200d"
                               u"\u23cf"
                               u"\u23e9"
                               u"\u231a"
                               u"\ufe0f"  # dingbats
                               u"\u3030"
                               "]+", re.UNICODE)
    return bool(regex_pattern.search(emoji))


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

