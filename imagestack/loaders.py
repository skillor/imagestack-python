import cv2
import os
from PIL import ImageFont


class ImageLoader:
    def load_into(self, func):
        raise Exception('Raw usage of Image Loader forbidden, use FileImageLoader')


class FileImageLoader(ImageLoader):
    def __init__(self, file=None, prefix=''):
        self.file = file
        self.prefix = prefix

    def load_into(self, func):
        img = cv2.imread(self.file, cv2.IMREAD_UNCHANGED)
        func(self.prefix + '/' + os.path.basename(self.file), img)


class DirectoryImageLoader(ImageLoader):
    def __init__(self, directory=None, prefix=''):
        self.directory = directory
        self.prefix = prefix

    def load_into(self, func):
        for f in os.listdir(self.directory):
            if f.endswith('.png'):
                img = cv2.imread(os.path.join(self.directory, f), cv2.IMREAD_UNCHANGED)
                img = cv2.cvtColor(img, cv2.COLOR_RGB2RGBA)
                func(self.prefix + '/' + f, img)


class FontLoader:
    def __init__(self, fonts=None, max_fonts_loaded=10):
        self.registered_fonts = {}
        self.loaded_fonts = {}
        self.max_fonts_loaded = max_fonts_loaded

        if fonts is not None:
            for k, v in fonts.items():
                self.registered_fonts[k] = v

    def load_font(self, font_name, size):
        if font_name not in self.registered_fonts:
            raise Exception('Error font: "' + font_name + '" was not found!')

        if (font_name, size) not in self.loaded_fonts:

            if len(self.loaded_fonts) >= self.max_fonts_loaded:
                del self.loaded_fonts[min(self.loaded_fonts.items(), key=lambda x: x[1][1])[0]]

            font = ImageFont.truetype(self.registered_fonts[font_name], size)
            self.loaded_fonts[(font_name, size)] = [font, 1]
            return font
        else:
            self.loaded_fonts[(font_name, size)][1] += 1
            return self.loaded_fonts[(font_name, size)][0]
