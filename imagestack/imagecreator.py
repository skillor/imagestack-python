from imagestack.loaders import *

import asyncio
import threading


class AsyncEvent(asyncio.Event):
    def set(self):
        # TODO: _loop is not documented
        self._loop.call_soon_threadsafe(super().set)


class ImageCreator:
    def __init__(self,
                 fonts=None,
                 load_memory=None,
                 emoji_path=None,
                 emoji_not_found_image=None,
                 download_emojis=False,
                 save_downloaded_emojis=True,
                 download_emoji_provider='microsoft'
                 ):
        self.font_loader = FontLoader(fonts)

        if emoji_path is None:
            emoji_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                      '..',
                                                      'images',
                                                      'emojis'))
        self.emoji_path = emoji_path

        if emoji_not_found_image is None:
            emoji_not_found_image = os.path.join(emoji_path, '0.png')

        self.emoji_not_found_image = emoji_not_found_image
        self.download_emojis = download_emojis
        self.save_downloaded_emojis = save_downloaded_emojis
        self.download_emoji_provider = download_emoji_provider

        if load_memory is None:
            load_memory = []

        self.image_memory = {}
        for loader in load_memory:
            loader.load_into(self.add_to_memory)

    def add_to_memory(self, name, img):
        if name in self.image_memory:
            raise Exception('image with same name was loaded before! Use a prefix')
        self.image_memory[name] = img

    async def create(self, stack, max_size=(-1, -1)):
        if stack is None:
            return None

        class _CreateImage:
            def __init__(_self, event):
                _self.result = None
                _self.event = event

            def create(_self):
                loop = asyncio.new_event_loop()
                loop.run_until_complete(_self._async_create())

            async def _async_create(_self):
                _self.result = await stack.create_bytes(image_creator=self, max_size=max_size)
                _self.event.set()

        e = AsyncEvent()
        ci = _CreateImage(e)

        threading.Thread(target=ci.create).start()
        await e.wait()

        return ci.result

    def create_html(self, stack):
        return stack.create_html(image_creator=self)
