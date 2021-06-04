from . import *
import requests
import cv2
import numpy as np
from textwrap import wrap
import unicodedata


class Createable:
    pass


class AlignLayer(VariableKwargManager, Createable):
    def accept(self, visitor):
        return visitor.visit_AlignLayer(self)

    def _init(self):
        self.pos = self.get_kwarg('pos', (0, 0))
        self.align_x = self.get_kwarg('align_x', 'left')
        self.align_y = self.get_kwarg('align_y', 'top')
        self.max_size = self.get_kwarg('max_size', (-1, -1))

    def html_position_style(self):
        rel_x, rel_y = html_relative_position(self.max_size, self.align_x, self.align_y)
        pos_x = self.pos[0] + rel_x
        pos_y = self.pos[1] + rel_y
        return 'position:absolute;overflow:clip;left:{}px;top:{}px;text-align:{};'.format(pos_x, pos_y, self.align_x)

    def html_style(self):
        style = self.html_position_style()
        if self.max_size[0] >= 0:
            style += 'max-width:{}px;'.format(self.max_size[0])
        if self.max_size[1] >= 0:
            style += 'max-height:{}px;'.format(self.max_size[1])
        return style


class ColoredLayer(AlignLayer):
    def accept(self, visitor):
        return visitor.visit_ColoredLayer(self)

    def _init(self):
        super()._init()
        self.color = self.get_kwarg('color', (0, 0, 0, 0))
        if not issubclass(type(self.color), ColorInterface):
            self.color = SingleColor(self.color)

    def colored(self, img):
        color_overlay = self.color.create(img.shape)
        color_overlay[..., 3] = img[..., 3] * (color_overlay[..., 3] / 255.0)
        return color_overlay

    def html_style(self):
        return super().html_style() + self.color.html_style_background()


class ColorLayer(ColoredLayer):
    def accept(self, visitor):
        return visitor.visit_ColorLayer(self)

    def _init(self):
        super()._init()
        self.resize = self.get_kwarg('resize', (1, 1))
        super()._init_finished()

    def html_style(self):
        return super().html_style() + size_to_html(self.resize, self)


class EmptyLayer(ColorLayer):
    def accept(self, visitor):
        return visitor.visit_EmptyLayer(self)


class ImageLayer(AlignLayer):
    def accept(self, visitor):
        return visitor.visit_ImageLayer(self)

    def _init(self):
        super()._init()
        self.resize = self.get_kwarg('resize', False)

    def validated(self, img):
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGBA)
        elif img.shape[2] == 3:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2RGBA)
        return img

    def resized(self, img):
        if self.resize is False:
            return img
        return cv2.resize(img, self.resize)

    def html_image(self, url):
        return '<img src="{}" style="width:{}px;height:{}px;" />'.format(url, self.resize[0], self.resize[1])


class FileImageLayer(ImageLayer):
    def accept(self, visitor):
        return visitor.visit_FileImageLayer(self)

    def _init(self):
        super()._init()
        self.file = self.get_kwarg('file')
        super()._init_finished()


class MemoryImageLayer(ImageLayer):
    def accept(self, visitor):
        return visitor.visit_MemoryImageLayer(self)

    def _init(self):
        super()._init()
        self.memory = self.get_kwarg('memory')
        super()._init_finished()


class EmojiLayer(ImageLayer):
    base_emoji_url = 'http://emojipedia.org/'

    def accept(self, visitor):
        return visitor.visit_EmojiLayer(self)

    def _init(self):
        super()._init()
        self.emoji = self.get_kwarg('emoji')
        if not is_emoji(self.emoji):
            self.emoji = '🆘'
        super()._init_finished()

    def html_style(self):
        return 'font-family: Segoe UI Emoji, Segoe UI Symbol, Symbola, Quivira;font-size:{}px;'\
                   .format(max(0, self.resize[0], self.resize[1]) * 0.75) + self.html_position_style()

    def get_emoji_image_url(self, provider):
        r = requests.get(self.base_emoji_url + self.emoji)
        for x in r.text.split('data-src="')[1:]:
            url = x.split('"')[0]
            if '/{}/'.format(provider) in url:
                return url


class WebImageLayer(ImageLayer):
    def accept(self, visitor):
        return visitor.visit_WebImageLayer(self)

    def _init(self):
        super()._init()
        self.url = self.get_kwarg('url')
        super()._init_finished()


class TextLayer(ColoredLayer):
    def accept(self, visitor):
        return visitor.visit_TextLayer(self)

    def _init(self):
        super()._init()
        self.font = self.get_kwarg('font', 'default')
        self.font_size = self.get_kwarg('font_size', 16)

        self.line_margin = self.get_kwarg('line_margin', 0)

        self.text_align = self.get_kwarg('text_align', 'left')

        self.text_lines = self.get_kwarg('text_lines', False)
        if self.text_lines is False:
            text = self.get_kwarg('text')
            text = unicodedata.normalize('NFKC', str(text))
            self.wrap_limit = self.get_kwarg('wrap_limit', -1)

            if self.wrap_limit > 0:
                self.text_lines = wrap(text, self.wrap_limit)
            else:
                self.text_lines = [text]

        for i in range(len(self.text_lines)):
            self.text_lines[i] = unicodedata.normalize('NFKC', str(self.text_lines[i]))

        super()._init_finished()

    def get_text_dimensions(self, font):
        ascent, descent = font.getmetrics()

        line_heights = [
            ascent + self.line_margin
            for _ in self.text_lines
        ]

        line_widths = [
            font.getmask(text_line).getbbox()[2]
            for text_line in self.text_lines
        ]

        total_height = sum(line_heights)

        total_width = max(line_widths)

        return total_width, total_height, line_widths, line_heights, descent

    def lines_html(self):
        line_template = '<p style="max-width:{}px;margin:0 0 {}px 0;text-overflow:ellipsis;' \
                        'white-space:nowrap;overflow-x:clip;overflow-y:visible;line-height:{}px;">{{}}</p>'\
            .format(self.max_size[0], self.line_margin, self.font_size)
        return '<div style="display:inline-block;text-align:{};{}">{}</div>'\
            .format(
                self.text_align,
                self.color.html_style_color(),
                ''.join(map(line_template.format, self.text_lines))
            )

    def html_style(self):
        style = '{}' \
                '{}' \
                'font-family:\'{}\';' \
                'font-size:{}px;' \
            .format(
                self.html_position_style(),
                size_to_html(self.max_size, self),
                self.font,
                self.font_size
            )
        return style


class LineLayer(ColoredLayer):
    def accept(self, visitor):
        return visitor.visit_LineLayer(self)

    def _init(self):
        super()._init()
        self.target = self.get_kwarg('target')
        self.line_width = self.get_kwarg('line_width', -1)
        super()._init_finished()


class RectangleLayer(ColoredLayer):
    def accept(self, visitor):
        return visitor.visit_RectangleLayer(self)

    def _init(self):
        super()._init()
        self.size = self.get_kwarg('size', (0, 0))
        self.radius = self.get_kwarg('radius', 0)
        self.line_width = self.get_kwarg('line_width', -1)
        super()._init_finished()


class ProgressLayer(RectangleLayer):
    def accept(self, visitor):
        return visitor.visit_ProgressLayer(self)

    def _init(self):
        direction = self.get_kwarg('direction', 'x')
        percentage = self.get_kwarg('percentage', 1.0)

        size = self.get_kwarg('size')
        if direction == 'y':
            self.set_kwarg('size', (size[0], int(size[1] * percentage)))
        else:
            self.set_kwarg('size', (int(size[0] * percentage), size[1]))

        super()._init()


class PieLayer(ColoredLayer):
    def accept(self, visitor):
        return visitor.visit_PieLayer(self)

    def _init(self):
        super()._init()
        self.radius = self.get_kwarg('radius', 0)
        self.border_width = self.get_kwarg('border_width', 1)
        self.line_width = self.get_kwarg('line_width', 1)
        self.choices = self.get_kwarg('choices')
        self.choices_radius = self.get_kwarg('choices_radius', (self.radius - self.border_width) * 0.75)
        self.rotate_choices = self.get_kwarg('rotate_choices', True)
        super()._init_finished()


class ListLayer(AlignLayer):
    def accept(self, visitor):
        return visitor.visit_ListLayer(self)

    def _init(self):
        super()._init()
        self.repeat = self.get_kwarg('repeat')
        self.template = self.get_kwarg('template')
        self.direction = self.get_kwarg('direction', 'y')
        self.margin = self.get_kwarg('margin', 0)
        super()._init_finished()

    def concat(self, img1, img2):
        if img1 is None:
            return img2
        elif img2 is None:
            return img1
        if self.direction == 'x':
            return cv2.hconcat([img1, img2])
        return cv2.vconcat([img1, img2])

    def concat_margin(self, img):
        if self.direction == 'x':
            return cv2.hconcat([img, np.zeros((img.shape[0], self.margin, img.shape[2]), dtype=np.uint8)])
        return cv2.vconcat([img, np.zeros((self.margin, img.shape[1], img.shape[2]), dtype=np.uint8)])
