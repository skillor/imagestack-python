from . import *
from .visitor import Visitor
import numpy as np
import cv2
import os
import requests
import warnings
from PIL import Image, ImageDraw


class VisitorCreate(Visitor):
    def __init__(self, image_creator):
        self.image_creator = image_creator

    def visit_ImageStack(self, el):
        img = None
        for layer in el.layers:
            fg = layer.accept(self)

            img = overlay(img, fg, layer.pos[0], layer.pos[1], layer.max_size, layer.align_x, layer.align_y)
        return img

    def visit_AnimatedImageStack(self, el):
        el.animated._init()
        el.animated.create_init(self)

        fgimage = None
        if el.static_fg is not False:
            el.static_fg._init()
            fgimage = self.visit_ImageStack(el.static_fg)
            fgimage = cv2.cvtColor(fgimage, cv2.COLOR_RGBA2BGRA)

        bgimage = None
        if el.static_bg is not False:
            el.static_bg._init()
            bgimage = self.visit_ImageStack(el.static_bg)
            bgimage = cv2.cvtColor(bgimage, cv2.COLOR_RGBA2BGRA)

        image_data = []
        for i in list(np.arange(0, 1, 1 / (el.fps * el.seconds))) + [1]:
            t = el.animated.create_progress(i)
            t = overlay(bgimage, t)
            t = overlay(t, fgimage)

            t = Image.fromarray(t)

            image_data.append(t)

        return image_data

    def visit_AlignLayer(self, el):
        raise Exception('Raw usage of AlignLayer.create is forbidden!')

    def visit_ColoredLayer(self, el):
        raise Exception('Raw usage of ColoredLayer.create is forbidden, use ColorLayer!')

    def visit_ColorLayer(self, el):
        return el.colored(np.full((el.resize[1], el.resize[0], 4), ALPHA_COLOR, dtype=np.uint8))

    def visit_EmptyLayer(self, el):
        return self.visit_ColorLayer(el)

    def visit_ImageLayer(self, el):
        raise Exception('Raw usage of ImageLayer.create forbidden, use FileImageLayer')

    def visit_FileImageLayer(self, el):
        img = cv2.imread(el.file, cv2.IMREAD_UNCHANGED)
        img = el.validated(img)
        return el.resized(img)

    def visit_MemoryImageLayer(self, el):
        img = self.image_creator.image_memory[el.memory]
        img = el.validated(img)
        return el.resized(img)

    def visit_WebImageLayer(self, el):
        img_bytes = requests.get(el.url).content
        img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_UNCHANGED)
        if img is None:
            return None
        img = el.validated(img)
        return el.resized(img)

    def visit_EmojiLayer(self, el):
        emoji_id = from_char(el.emoji)

        file = None
        if self.image_creator.emoji_path is not None:
            file = os.path.join(self.image_creator.emoji_path, emoji_id + '.png')
        img = None
        if file is not None and os.path.exists(file):
            img = cv2.imread(file, cv2.IMREAD_UNCHANGED)
        elif self.image_creator.download_emojis:
            url = el.get_emoji_image_url(self.image_creator.download_emoji_provider)
            if url is None:
                warnings.warn('Emoji "{}" was not found on "{}"!'.format(el.emoji, el.base_emoji_url))
            else:
                img_bytes = requests.get(url).content
                img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_UNCHANGED)
                if self.image_creator.save_downloaded_emojis:
                    cv2.imwrite(file, img)

        if img is None:
            if self.image_creator.emoji_not_found_image is not None and \
                    os.path.exists(self.image_creator.emoji_not_found_image):
                img = cv2.imread(self.image_creator.emoji_not_found_image, cv2.IMREAD_UNCHANGED)
            else:
                return None

        img = el.validated(img)
        return el.resized(img)

    def visit_TextLayer(self, el):
        if sum(map(len, el.text_lines)) == 0:
            return None

        font = self.image_creator.font_loader.load_font(el.font, el.font_size)

        total_width, total_height, line_widths, line_heights, descent = el.get_text_dimensions(font)

        img = Image.new("RGBA", (total_width, total_height), color=(0, 0, 0, 0))

        draw = ImageDraw.Draw(img)

        draw.fontmode = "L"

        y = 0
        for i in range(len(el.text_lines)):
            x = 0
            if el.text_align == 'center':
                x = int(total_width / 2 - line_widths[i] / 2)
            elif el.text_align == 'right':
                x = total_width - line_widths[i]
            draw.text((x, y - descent), el.text_lines[i], ALPHA_COLOR, font=font)
            y += line_heights[i]

        return el.colored(np.array(img))

    def visit_LineLayer(self, el):
        src = np.zeros((abs(el.target[1]), abs(el.target[0]), 4), dtype=np.uint8)
        start = [0, 0]
        end = [abs(el.target[0]), abs(el.target[1])]
        if el.target[0] < 0:
            start[0] = end[0]
            end[0] = 0
        if el.target[1] < 0:
            start[1] = end[1]
            end[1] = 0

        cv2.line(src, start, end, ALPHA_COLOR, el.line_width, LINE_TYPE)
        return el.colored(src)

    def visit_RectangleLayer(self, el):
        diameter = el.radius * 2

        thick_offset = max(0, el.line_width)
        double_thickoff = max(1, thick_offset * 2)

        mthick_offset = max(1, thick_offset)
        top_left = (thick_offset, thick_offset)
        bottom_right = (max(1, diameter - mthick_offset, el.size[1] - mthick_offset),
                        max(1, diameter - mthick_offset, el.size[0] - mthick_offset))

        src = np.zeros((bottom_right[0] + double_thickoff, bottom_right[1] + double_thickoff, 4), dtype=np.uint8)

        #  corners:
        #  p1 - p2
        #  |     |
        #  p4 - p3

        p1 = top_left
        p2 = (bottom_right[1], top_left[1])
        p3 = (bottom_right[1], bottom_right[0])
        p4 = (top_left[0], bottom_right[0])

        corner_radius = abs(el.radius)
        thickness = el.line_width

        if thickness < 0:
            # big rect
            start_pos = (p1[0] + corner_radius, p1[1])
            end_pos = (p3[0] - corner_radius, p3[1])
            cv2.rectangle(src, start_pos, end_pos, ALPHA_COLOR, thickness=thickness, lineType=LINE_TYPE)
            start_pos = (p1[0], p1[1] + corner_radius)
            end_pos = (p3[0], p3[1] - corner_radius)
            cv2.rectangle(src, start_pos, end_pos, ALPHA_COLOR, thickness=thickness, lineType=LINE_TYPE)

        else:
            # draw straight lines
            cv2.line(src, (p1[0] + corner_radius, p1[1]), (p2[0] - corner_radius, p2[1]), ALPHA_COLOR, thickness,
                     LINE_TYPE)
            cv2.line(src, (p2[0], p2[1] + corner_radius), (p3[0], p3[1] - corner_radius), ALPHA_COLOR, thickness,
                     LINE_TYPE)
            cv2.line(src, (p3[0] - corner_radius, p4[1]), (p4[0] + corner_radius, p3[1]), ALPHA_COLOR, thickness,
                     LINE_TYPE)
            cv2.line(src, (p4[0], p4[1] - corner_radius), (p1[0], p1[1] + corner_radius), ALPHA_COLOR, thickness,
                     LINE_TYPE)

        if corner_radius > 0:
            # draw arcs
            cv2.ellipse(src, (p1[0] + corner_radius, p1[1] + corner_radius), (corner_radius, corner_radius),
                        180.0, 0, 90, ALPHA_COLOR, thickness, LINE_TYPE)
            cv2.ellipse(src, (p2[0] - corner_radius, p2[1] + corner_radius), (corner_radius, corner_radius),
                        270.0, 0, 90, ALPHA_COLOR, thickness, LINE_TYPE)
            cv2.ellipse(src, (p3[0] - corner_radius, p3[1] - corner_radius), (corner_radius, corner_radius),
                        0.0, 0, 90, ALPHA_COLOR, thickness, LINE_TYPE)
            cv2.ellipse(src, (p4[0] + corner_radius, p4[1] - corner_radius), (corner_radius, corner_radius),
                        90.0, 0, 90, ALPHA_COLOR, thickness, LINE_TYPE)

        if el.radius < 0:
            src = invert_image(src)

        return el.colored(src)

    def visit_ProgressLayer(self, el):
        return self.visit_RectangleLayer(el)

    def visit_PieLayer(self, el):
        angle_offset = 270

        diameter = el.radius * 2
        radius = el.radius
        half_border_width = int(el.border_width * 0.5)

        adjusted_radius = radius - half_border_width - 1

        center = (radius, radius)

        src = np.zeros((diameter, diameter, 4), dtype=np.uint8)

        slices = len(el.choices)
        slice_size = int(360 / slices)
        half_slice_size = int(slice_size * 0.5)

        cv2.circle(src,
                   center,
                   adjusted_radius,
                   ALPHA_COLOR,
                   el.border_width)

        for i in range(slices):
            start = point_on_circle(angle=slice_size * i + angle_offset,
                                    radius=adjusted_radius,
                                    center=center)

            cv2.line(src,
                     start,
                     center,
                     ALPHA_COLOR,
                     el.line_width,
                     LINE_TYPE)

        img = el.colored(src)

        for i in range(slices):
            c = point_on_circle(angle=slice_size * i + half_slice_size + angle_offset,
                                radius=int(el.choices_radius),
                                center=center)

            el.choices[i]._init()
            cimg = el.choices[i].accept(self)

            if cimg is not None:
                if el.rotate_choices:
                    cimg = rotate_image(cimg, angle=-(slice_size * i + half_slice_size), padding=True)

                ho1, wo1 = int(cimg.shape[0] * 0.5), int(cimg.shape[1] * 0.5)
                ho2, wo2 = cimg.shape[0] - ho1, cimg.shape[1] - wo1
                img[c[1] - ho1:c[1] + ho2, c[0] - wo1:c[0] + wo2] = cimg

        return img

    def visit_ListLayer(self, el):
        img = None
        for i in range(el.repeat):
            el.template._init()
            img = el.concat(img, el.template.accept(self))
            if i < el.repeat - 1:
                img = el.concat_margin(img)

        return img
