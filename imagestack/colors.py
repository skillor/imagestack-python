import numpy as np


class ColorInterface:
    @staticmethod
    def validated(color):
        if isinstance(color, tuple) or isinstance(color, list):
            return SingleColor(color)
        return color

    def create(self, size):
        raise Exception('Raw usage of ColorInterface forbidden!')


class SingleColor(ColorInterface, np.ndarray):
    def __new__(cls, color):
        color = [max(0, min(255, x)) for x in color]
        if len(color) == 0:
            color = (0, 0, 0, 0)
        elif len(color) == 1:
            color = (color[0], color[0], color[0], 255)
        elif len(color) == 2:
            color = (color[0], color[0], color[0], color[1])
        elif len(color) == 3:
            color = (color[2], color[1], color[0], 255)
        elif len(color) >= 4:
            color = (color[2], color[1], color[0], color[3])
        return np.array(color).view(cls)

    def get(self):
        return self

    def lightened(self, factor):
        return SingleColor([self[2] * factor, self[1] * factor, self[0] * factor, self[3]])

    def darkened(self, factor):
        return self.lightened(1 - factor)

    def alpha(self, alpha):
        return SingleColor([self[2], self[1], self[0], alpha])

    def to_bgra(self):
        return SingleColor([self[2], self[1], self[0], self[3]])

    def create(self, size):
        return np.full((size[0], size[1], self.shape[0]), self, dtype=np.uint8)

    def svg_color_definition(self):
        return '<linearGradient id="color"><stop stop-color="{}"/></linearGradient>'.format(self.html_color())

    def html_color(self):
        return 'rgba({},{},{},{})'.format(self[2], self[1], self[0], self[3] / 255)

    def html_style_color(self):
        return 'color:{};'.format(self.html_color())

    def html_style_background(self):
        return 'background-color:{};'.format(self.html_color())

    def is_fully_transparent(self):
        return self[3] == 0


class LinearGradientColor(ColorInterface):
    def __init__(self, color1, color2, axis=0):
        self.color1 = self.validated(color1)
        self.color2 = self.validated(color2)
        self.direction_axis = axis

    def color_mix(self, mix):
        return (1 - mix) * self.color1.get() + mix * self.color2.get()

    def create(self, size):
        if self.direction_axis == 0:
            size = (size[1], size[0])

        lin = np.linspace(0, 1, size[1], dtype=np.float16)
        color_gradient = np.array(list(map(self.color_mix, lin)), dtype=np.uint8)
        color_gradient = np.repeat(color_gradient[:, np.newaxis], size[0], axis=1)

        if self.direction_axis == 1:
            color_gradient = color_gradient.swapaxes(0, 1)

        return color_gradient

    def svg_color_definition_with_id(self, color_id):
        gradient_transform = ''
        if self.direction_axis == 0:
            gradient_transform = ' gradientTransform="rotate(90)"'
        return '<linearGradient id="{}"{}>' \
               '<stop offset="0%" style="stop-color:{};"/>' \
               '<stop offset="100%" style="stop-color:{};"/>' \
               '</linearGradient>'.format(color_id,
                                          gradient_transform,
                                          self.color1.html_color(),
                                          self.color2.html_color(),
                                          )

    def svg_color_definition(self):
        return self.svg_color_definition_with_id('color')

    def html_color(self):
        direction = 'to right'
        if self.direction_axis == 0:
            direction = 'to bottom'
        return 'linear-gradient({}, {}, {})'.format(direction,
                                                    self.color1.html_color(),
                                                    self.color2.html_color()
                                                    )

    def html_style_color(self):
        return 'background-image:{};' \
               'background-size:100%;' \
               '-webkit-background-clip:text;' \
               '-moz-background-clip:text;' \
               '-webkit-text-fill-color:transparent;' \
               '-moz-text-fill-color:transparent;'.format(self.html_color())

    def html_style_background(self):
        return 'background-image:{};'.format(self.html_color())

    def is_fully_transparent(self):
        return self.color1.is_fully_transparent() and self.color1.is_fully_transparent()
