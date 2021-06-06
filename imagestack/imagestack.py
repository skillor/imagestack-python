from . import *
from .visitor_create import VisitorCreate
from .visitor_html import VisitorHtml
import io
import cv2
import numpy as np


class ImageStack(Createable, VariableKwargManager):
    def accept(self, visitor):
        return visitor.visit_ImageStack(self)

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        if len(args) > 1:
            self.set_kwarg('layers', list(args))
        elif len(args) == 1 and isinstance(args[0], list):
            self.set_kwarg('layers', args[0])

    def _init(self):
        self.layers = self.get_kwarg('layers', [])
        if len(self.layers) == 0:
            self.layers = [EmptyLayer()]

        for layer in self.layers:
            layer._init()
        super()._init_finished()

    async def create(self, image_creator, max_size=None):
        v = VisitorCreate(image_creator)
        img = self.accept(v)

        resize_factor = 1
        if max_size is not None:
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
        v = VisitorHtml(image_creator)
        return self.accept(v)


class AnimatedImageStack(Createable, VariableKwargManager):
    def accept(self, visitor):
        return visitor.visit_AnimatedImageStack(self)

    def _init(self):
        self.rotate = self.get_kwarg('rotate')
        self.static_fg = self.get_kwarg('static_fg', False)
        self.static_bg = self.get_kwarg('static_bg', False)
        self.seconds = self.get_kwarg('seconds', 5)
        self.fps = self.get_kwarg('fps', 5)
        self.rotation_func = self.get_kwarg('rotation_func', lambda i: self.get_kwarg('rotation', None) * i)
        self.rotation_id = 'rotate-{}-{}-{}'.format(int(self.rotation_func(0.35)),
                                                    int(self.rotation_func(0.62)),
                                                    int(self.rotation_func(0.88)))
        self.loop = self.get_kwarg('loop', 1)
        self.bg_color = self.get_kwarg('bg_color', (0, 0, 0, 0))
        if len(self.bg_color) == 3:
            self.bg_color = self.bg_color[0], self.bg_color[1], self.bg_color[2], 255

    async def create(self, image_creator):
        v = VisitorCreate(image_creator)
        image_data = self.accept(v)
        return image_data

    async def create_bytes(self, image_creator):
        image_data = await self.create(image_creator)

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

    def create_html(self, image_creator):
        v = VisitorHtml(image_creator)
        return self.accept(v)
