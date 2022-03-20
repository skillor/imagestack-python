from . import *
import os
import asyncio
import threading

from . import to_char


class AsyncEvent(asyncio.Event):
    def set(self):
        # TODO: _loop is not documented
        self._loop.call_soon_threadsafe(super().set)


class ImageCreator:
    def __init__(self,
                 fonts=None,
                 load_memory=None,
                 emoji_path=None,
                 emoji_fallback='🆘',
                 download_emojis=False,
                 save_downloaded_emojis=False,
                 download_emoji_provider='microsoft'
                 ):
        self.font_loader = FontLoader(fonts)

        self.save_downloaded_emojis = save_downloaded_emojis
        if emoji_path is None:
            self.save_downloaded_emojis = False
        self.emoji_path = emoji_path

        self.emoji_fallback = emoji_fallback

        self.download_emojis = download_emojis
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

    def get_downloaded_emojis(self):
        if not self.save_downloaded_emojis:
            return []
        emojis = []
        for e in os.listdir(self.emoji_path):
            try:
                emoji = to_char(os.path.splitext(e)[0])
                if is_emoji(emoji):
                    emojis.append({'emoji': emoji, 'path': e})
            except:
                pass
        return emojis

    async def create(self, stack, max_size=(-1, -1)):
        if stack is None:
            return None

        class _CreateImage:
            def __init__(_self, event):
                _self.result = None
                _self.error = None
                _self.event = event

            def create(_self):
                loop = asyncio.new_event_loop()
                loop.run_until_complete(_self._async_create())

            async def _async_create(_self):
                try:
                    _self.result = await stack.create_bytes(image_creator=self, max_size=max_size)
                except Exception as err:
                    _self.error = err
                _self.event.set()

        e = AsyncEvent()
        ci = _CreateImage(e)

        threading.Thread(target=ci.create).start()
        await e.wait()
        if ci.error is not None:
            raise ci.error

        return ci.result

    def create_html(self, stack):
        return stack.create_html(image_creator=self)

    def create_raw_html(self, stack):
        return stack.create_raw_html(image_creator=self)
