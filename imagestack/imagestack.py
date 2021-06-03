from .layers import Createable, EmptyLayer
from .variables import VariableKwargManager
from .helpers import *
from .visitor_create import VisitorCreate
from .visitor_html import VisitorHtml
import base64
import io


class ImageStack(Createable, VariableKwargManager):
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        if len(args) > 1:
            self.set_kwarg('layers', list(args))
        elif len(args) == 1 and isinstance(args[0], list):
            self.set_kwarg('layers', args[0])

    def _init(self):
        self.layers = self.get_kwarg('layers', [])
        for layer in self.layers:
            layer._init()
        super()._init_finished()

    async def create(self, image_creator, max_size):
        img = None
        layers = self.layers
        if len(layers) == 0:
            layers = [EmptyLayer()]

        v = VisitorCreate(image_creator)

        for layer in layers:
            fg = layer.accept(v)

            img = overlay(img, fg, layer.pos[0], layer.pos[1], layer.max_size, layer.align_x, layer.align_y)

        resize_factor = 1
        if 0 < max_size[0] < img.shape[1]:
            resize_factor = max_size[0] / img.shape[1]
        if 0 < max_size[1] < img.shape[0]:
            resize_factor = min(resize_factor, max_size[1] / img.shape[0])

        if resize_factor < 1:
            img = cv2.resize(img, (int(img.shape[1] * resize_factor), int(img.shape[0] * resize_factor)))
        return img

    async def create_bytes(self, image_creator, max_size):
        img = await self.create(image_creator, max_size)

        is_success, buffer = cv2.imencode('.png', img)
        return io.BytesIO(buffer)

    def create_html(self, image_creator):
        style_html = []
        for key, font_path in image_creator.font_loader.registered_fonts.items():
            with open(font_path, "rb") as font_file:
                base64_font = base64.b64encode(font_file.read()).decode('ascii')
            style_html.append('@font-face {{'
                              'font-family:\'{}\';'
                              'src:url(data:application/x-font-woff;charset=utf-8;base64,{}) format(\'woff\');'
                              '}}'
                              .format(key, base64_font))

        layers_html = []

        v = VisitorHtml(image_creator)

        for layer in self.layers:
            layers_html.append(layer.accept(v))
        return '<style>{}</style><div>{}</div>'.format(''.join(style_html), ''.join(layers_html))


class AnimatedImageStack(Createable, VariableKwargManager):
    def _init(self):
        self.rotate = self.get_kwarg('rotate')
        self.static_fg = self.get_kwarg('static_fg', False)
        self.static_bg = self.get_kwarg('static_bg', False)
        self.seconds = self.get_kwarg('seconds', 5)
        self.fps = self.get_kwarg('fps', 5)
        self.rotation_func = self.get_kwarg('rotation_func', lambda i: self.get_kwarg('rotation', None) * i)
        self.loop = self.get_kwarg('loop', 1)
        self.bg_color = self.get_kwarg('bg_color', (0, 0, 0, 0))
        if len(self.bg_color) == 3:
            self.bg_color = self.bg_color[0], self.bg_color[1], self.bg_color[2], 255

    async def create(self, image_creator, **kwargs):
        rimage = await self.rotate.raw_create(image_creator, **kwargs)
        rimage = cv2.cvtColor(rimage, cv2.COLOR_RGBA2BGRA)

        fgimage = None
        if self.static_fg is not False:
            fgimage = await self.static_fg.raw_create(image_creator, **kwargs)
            fgimage = cv2.cvtColor(fgimage, cv2.COLOR_RGBA2BGRA)

        bgimage = None
        if self.static_bg is not False:
            bgimage = await self.static_bg.raw_create(image_creator, **kwargs)
            bgimage = cv2.cvtColor(bgimage, cv2.COLOR_RGBA2BGRA)

        def normalize_angle(a):
            a = int(a)
            while a < 0:
                a += 360
            while a >= 360:
                a -= 360
            return a

        buffered_images = {}

        image_data = []
        for i in np.arange(0, 1, 1 / (self.fps * self.seconds)):
            angle = normalize_angle(self.rotation_func(i))
            hit = None
            if len(buffered_images) > 0:
                hit = min(buffered_images.keys(), key=lambda x: abs(x - angle))
            if hit is not None and abs(angle - hit) <= 1:
                image_data.append(buffered_images[hit])
            else:
                t = rotate_image(rimage, angle, bg_color=self.bg_color)
                t = overlay(bgimage, t)
                t = overlay(t, fgimage)

                t = Image.fromarray(t)

                buffered_images[angle] = t

                image_data.append(t)

        gif_image_bytes = io.BytesIO()

        kwargs = {
            'fp': gif_image_bytes,
            'format': 'gif',
            'save_all': True,
            'append_images': image_data[1:],
            'duration': int(1000 / self.fps),
            # 'transparency': 0,
            'disposal': 3,
        }
        if self.loop != 1:
            kwargs['loop'] = self.loop

        image_data[0].save(**kwargs)

        gif_image_bytes.seek(0)

        is_success, last_image_bytes = cv2.imencode('.png', cv2.cvtColor(np.array(image_data[-1]), cv2.COLOR_RGBA2BGRA))

        return gif_image_bytes, io.BytesIO(last_image_bytes)
