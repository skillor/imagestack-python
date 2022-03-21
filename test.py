import asyncio
import unittest
import cv2
import numpy as np

from imagestack import *

SHOW_IMAGE = True


def call_async(cor):
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(cor)
    loop.close()
    return result


def show_image(img):
    if SHOW_IMAGE:
        cv2.imshow('test', img)
        cv2.waitKey(0)


class TestStringMethods(unittest.TestCase):
    def test_is_emoji(self):
        self.assertTrue(is_emoji('🎈'))

    def test_emoji_conversion(self):
        self.assertEqual(from_char('🎈'), 'f09f8e88')
        self.assertEqual(to_char('f09f8e88'), '🎈')
        self.assertEqual(to_char(from_char('🎈')), '🎈')

    def test_create_RectangleLayer_bytes(self):
        i = ImageStack([
            RectangleLayer(
                pos=(0, 0),
                size=(120, 120),
                color=(255, 255, 255, 128),
                radius=-60,
            )
        ])
        i._init()

        image_creator = ImageCreator()
        image_buffer = call_async(image_creator.create(i))
        self.assertGreater(len(image_buffer.read()), 1)

    def test_create_RectangleLayer_html(self):
        i = ImageStack([
            RectangleLayer(
                pos=(0, 0),
                size=(120, 120),
                color=(255, 255, 255, 128),
                radius=-60,
            )
        ])
        i._init()

        image_creator = ImageCreator()
        image_html = image_creator.create_html(i)
        self.assertGreater(len(image_html), 1)

    def test_resolve_string(self):
        s = '''ImageStack([
            RectangleLayer(
                pos=(0, 0),
                size=(120, 120),
                color=Variable(('member', 'top_role', 'color')),
                radius=-60,
            )
        ])'''
        r = ImageStackResolveString(s)({
            'member': {'top_role': {'color': (255, 255, 255)}}
        })

        image_creator = ImageCreator()
        image_buffer = call_async(image_creator.create(r))
        self.assertGreater(len(image_buffer.read()), 1)


if __name__ == '__main__':
    unittest.main()
