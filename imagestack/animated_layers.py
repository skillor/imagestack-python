from . import *
import cv2


class AnimatedCreateable:
    def create_init(self, visitor):
        pass

    def create_progress(self, i):
        pass


class RotationLayer(VariableKwargManager, AnimatedCreateable):
    def _init(self):
        self.rotate = self.get_kwarg('rotate')
        self.rotation_func = self.get_kwarg('rotation_func', lambda i: self.get_kwarg('rotation', None) * i)
        self.rotation_id = 'rotate-{}-{}-{}'.format(int(self.rotation_func(0.35)),
                                                    int(self.rotation_func(0.62)),
                                                    int(self.rotation_func(0.88)))
        self.bg_color = self.get_kwarg('bg_color', (0, 0, 0, 0))
        if len(self.bg_color) == 3:
            self.bg_color = self.bg_color[0], self.bg_color[1], self.bg_color[2], 255

        self.img = None

    def create_init(self, visitor):
        self.rotate._init()
        self.img = visitor.visit_ImageStack(self.rotate)
        self.img = cv2.cvtColor(self.img, cv2.COLOR_RGBA2BGRA)

    def create_progress(self, i):
        angle = normalize_angle(self.rotation_func(i))
        return rotate_image(self.img, angle, bg_color=self.bg_color)
