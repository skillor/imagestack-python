import asyncio
import unittest
from imagestack import ImageStackResolveString, ImageCreator
import cv2
import numpy as np


SHOW_IMAGE = True


def call_async(cor):
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(cor)
    loop.close()
    return result


def show_image(img):
    if SHOW_IMAGE:
        cv2.imshow('test', img)
        cv2.waitKey(0)


class TestStringMethods(unittest.TestCase):
    def test_resolve_string(self):
        s = '''ImageStack([
                RectangleLayer(
                    pos=(0, 0),
                    line_width=-1,
                    size=(600, 150),
                    radius=20,
                    color=(55, 50, 48),
                )])'''
        r = ImageStackResolveString(s)

    def test_make_image(self):
        s = '''ImageStack([
    # BG
    RectangleLayer(
        pos=(0, 0),
        line_width=-1,
        size=(200, 100),
        radius=20,
        color=(55, 50, 48),
    ),

    # BG Border
    RectangleLayer(
        pos=(0, 0),
        line_width=2,
        size=(200, 100),
        radius=20,
        color=LinearGradientColor(SingleColor((255, 0, 0)),
                                  SingleColor((0, 255, 0)),
                                  0),
    ),

    # RANKUP
    TextLayer(
        pos=(58, 13),
        font='bold',
        font_size=22,
        text='RANKUP',
        color=LinearGradientColor(SingleColor((255, 0, 0)),
                                  SingleColor((0, 255, 0)),
                                  1),
        max_size=(170, 25)
    ),

    EmojiLayer(
        pos=(58, 70),
        resize=(16, 16),
        emoji='🍕',
    ),

    EmojiLayer(
        pos=(125, 70),
        resize=(16, 16),
        emoji='🍕',
    ),

    ProgressLayer(
        pos=(82, 77),
        percentage=1,
        line_width=-1,
        size=(34, 4),
        radius=2,
        color=LinearGradientColor(SingleColor((255, 0, 0)),
                                  SingleColor((0, 255, 0)),
                                  1),
    ),

    TextLayer(
        pos=(53, 73),
        align_x='right',
        font='regular',
        font_size=12,
        text='Lvl. 10',
        color=SingleColor((255, 0, 0)),
        max_size=(50, 22)
    ),

    TextLayer(
        pos=(145, 73),
        font='regular',
        font_size=12,
        text='Lvl. 11',
        color=SingleColor((0, 255, 0)),
        max_size=(50, 22)
    ),

    TextLayer(
        pos=(100, 42),
        font='regular',
        font_size=13,
        align_x='center',
        text='Peter',
        color=(255, 255, 255),
        max_size=(180, 16)
    ),
])'''

        s2 = '''ImageStack([
    RectangleLayer(
        pos=(0, 0),
        line_width=-1,
        size=(600, 150),
        radius=20,
        color=(55, 50, 48),
    ),

    RectangleLayer(
        pos=(15, 15),
        size=(120, 120),
        color=(55, 50, 48),
        radius=-60,
    ),

    # Emoji
    EmojiLayer(
        pos=(147, 15),
        resize=(40, 40),
        emoji='🍕',
    ),

    # Pregressbar BG
    ProgressLayer(
        pos=(150, 115),
        percentage=1,
        line_width=-1,
        direction='x',
        size=(430, 20),
        radius=10,
        color=(87, 87, 87)
    ),

    # Progressbar
    ProgressLayer(
        pos=(150, 115),
        percentage=0.5,
        line_width=-1,
        direction='x',
        size=(430, 20),
        radius=10,
        color=LinearGradientColor((24, 110, 241, 255),
                                  (7, 222, 255, 255),
                                  1)
    ),

    # Username
    TextLayer(
        pos=(200, 39),
        align_y='center',
        font='regular',
        font_size=35,
        text='Peter',
        color=(102, 172, 47),
        max_size=(280, 35)
    ),

    # Lvl.
    TextLayer(
        pos=(150, 92),
        font='regular',
        font_size=22,
        text='Lvl.',
        color=(103, 103, 103),
        max_size=(30, 22)
    ),

    # Lvl-value
    TextLayer(
        pos=(188, 87),
        font='regular',
        font_size=28,
        text='50',
        color=(255, 255, 255),
        max_size=(100, 28)
    ),

    # Rank
    TextLayer(
        pos=(578, 24),
        align_x='right',
        font='bold',
        font_size=35,
        text='#5',
        color=(102, 172, 47),
        max_size=(90, 30)
    ),

    # Xp Multiplier
    TextLayer(
        pos=(580, 72),
        align_x='right',
        font='regular',
        font_size=20,
        text='2.00x',
        color=(102, 172, 47),
        max_size=(150, 20),
    ),

    TextLayer(
        pos=(580, 95),
        align_x='right',
        font='regular',
        font_size=18,
        text='10 / 50 XP',
        color=(170, 170, 170),
        max_size=(280, 18)
    )
])'''

        r = ImageStackResolveString(s2)

        image_creator = ImageCreator(fonts={
            'regular': 'D:\\Pythonprogs\\KGS-discordbot\\fonts\\Product_Sans_Regular.ttf',
            'bold': 'D:\\Pythonprogs\\KGS-discordbot\\fonts\\Product_Sans_Bold.ttf',
        })

        image_html = image_creator.create_html(r())
        with open('test.html', 'w', encoding='utf-8') as f:
            f.write(image_html)

        image_buffer = call_async(image_creator.create(r()))
        image_res = cv2.imdecode(np.frombuffer(image_buffer.read(), np.uint8), -1)

        show_image(image_res)

        self.assertTupleEqual(image_res.shape, (150, 600, 4))


if __name__ == '__main__':
    unittest.main()
