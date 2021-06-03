import base64


class VisitorHtml:
    def __init__(self, image_creator):
        self.image_creator = image_creator

    def style_html(self):
        style_html = []
        for key, font_path in self.image_creator.font_loader.registered_fonts.items():
            with open(font_path, "rb") as font_file:
                base64_font = base64.b64encode(font_file.read()).decode('ascii')
            style_html.append('@font-face {{'
                              'font-family:\'{}\';'
                              'src:url(data:application/x-font-woff;charset=utf-8;base64,{}) format(\'woff\');'
                              '}}'
                              .format(key, base64_font))
        return ''.join(style_html)

    def visit_ImageStack(self, el):
        layers_html = []
        for layer in el.layers:
            layers_html.append(layer.accept(self))
        return '<style>{}</style><div>{}</div>'.format(self.style_html(), ''.join(layers_html))

    def visit_AnimatedImageStack(self, el):
        return '<div data-layer="AnimatedImageStack">AnimatedImageStack not yet supported</div>'

    def visit_AlignLayer(self, el):
        return '<div data-layer="AlignLayer" style="{}"></div>'.format(el.html_style())

    def visit_ColoredLayer(self, el):
        return '<div data-layer="ColoredLayer" style="{}"></div>'.format(el.html_style())

    def visit_ColorLayer(self, el):
        return '<div data-layer="ColorLayer" style="{}"></div>'.format(el.html_style())

    def visit_EmptyLayer(self, el):
        return self.visit_ColorLayer(el)

    def visit_ImageLayer(self, el):
        return '<div data-layer="ImageLayer"></div>'

    def visit_FileImageLayer(self, el):
        return '<div data-layer="FileImageLayer"></div>'

    def visit_MemoryImageLayer(self, el):
        return '<div data-layer="MemoryImageLayer"></div>'

    def visit_WebImageLayer(self, el):
        return '<div data-layer="WebImageLayer" style="{}">{}</div>' \
            .format(el.html_style(), el.html_image(el.url))

    def visit_EmojiLayer(self, el):
        emoji_url = el.get_emoji_image_url(self.image_creator.download_emoji_provider)
        return '<div data-layer="EmojiLayer" style="{}">{}</div>' \
            .format(el.html_style(), el.html_image(emoji_url))

    def visit_TextLayer(self, el):
        inner_style = 'width:100%;height:100%;display:flex;'
        if el.align_x == 'center':
            inner_style += 'justify-content:center;'
        elif el.align_x == 'right':
            inner_style += 'justify-content:flex-end;'
        if el.align_y == 'center':
            inner_style += 'align-items:center;'
        elif el.align_y == 'bottom':
            inner_style += 'align-items:flex-end;'
        return '<div data-layer="TextLayer" style="{}"><div style="{}">{}</div></div>' \
            .format(el.html_style(), inner_style, el.lines_html())

    def visit_RectangleLayer(self, el):
        def _create_svg_points():
            half_line_width = int(el.line_width / 2)
            radius = abs(el.radius)
            return ['M{},{}'.format(half_line_width + radius, half_line_width),
                    'L{},{}'.format(el.size[0] - half_line_width - radius, half_line_width),
                    'A{},{} 0 0 1 {},{}'.format(radius,
                                                radius,
                                                el.size[0] - half_line_width,
                                                half_line_width + radius),
                    'L{},{}'.format(el.size[0] - half_line_width, el.size[1] - half_line_width - radius),
                    'A{},{} 0 0 1 {},{}'.format(radius,
                                                radius,
                                                el.size[0] - half_line_width - radius,
                                                el.size[1] - half_line_width),
                    'L{},{}'.format(half_line_width + radius, el.size[1] - half_line_width),
                    'A{},{} 0 0 1 {},{}'.format(radius,
                                                radius,
                                                half_line_width,
                                                el.size[1] - half_line_width - radius),
                    'L{},{}'.format(half_line_width, half_line_width + radius),
                    'A{},{} 0 0 1 {},{}'.format(radius,
                                                radius,
                                                half_line_width + radius,
                                                half_line_width)]

        if el.radius >= 0:
            if el.line_width <= 0:
                style = 'width:{}px;height:{}px;border-radius:{}px;border-style:solid;{}border-width:0px;{}'.format(
                    el.size[0],
                    el.size[1],
                    max(0, abs(el.radius) - 0.05),
                    el.html_position_style(),
                    el.color.html_style_background(),
                )
                return '<div data-layer="RectangleLayer" style="{}"></div>'.format(style)
            else:
                style = 'width:{}px;height:{}px;{}'.format(
                    el.size[0],
                    el.size[1],
                    el.html_position_style(),
                )
                inner_path = '<path d="{}" fill="none" stroke="url(#color)" stroke-width="{}"/>' \
                    .format(
                        ' '.join(_create_svg_points()),
                        el.line_width,
                    )
                return '<div data-layer="RectangleLayer"><svg style="{}"><defs>{}</defs>{}</svg></div>' \
                    .format(style,
                            el.color.svg_color_definition(),
                            inner_path)
        if el.line_width <= 0:
            style = 'width:{}px;height:{}px;{}'.format(
                el.size[0],
                el.size[1],
                el.html_position_style(),
            )
            points = [
                'M-1,-1',
                'L{},-1'.format(el.size[0] + 1),
                'L{},{}'.format(el.size[0] + 1, el.size[1] + 1),
                'L-1,{}'.format(el.size[1] + 1),
                'L-1,-1',
            ]
            inner_path = '<path d="{}" fill-rule="evenodd" fill="url(#color)" stroke="none"/>' \
                .format(
                    ' '.join(points + _create_svg_points()),
                )
            return '<div data-layer="RectangleLayer"><svg style="{}"><defs>{}</defs>{}</svg></div>'\
                .format(style,
                        el.color.svg_color_definition(),
                        inner_path)
        return '<div data-layer="RectangleLayer" style="width:{}px;height:{}px;background-color:black;color:red;{}">' \
               'negative radius in combination with line width not yet supported' \
               '</div>' \
            .format(el.size[0],
                    el.size[1],
                    el.html_position_style())

    def visit_LineLayer(self, el):
        return '<div data-layer="LineLayer"></div>'

    def visit_ProgressLayer(self, el):
        return '<div data-layer="ProgressLayer">{}</div>'.format(self.visit_RectangleLayer(el))

    def visit_PieLayer(self, el):
        return '<div data-layer="PieLayer"></div>'

    def visit_ListLayer(self, el):
        return '<div data-layer="ListLayer"></div>'
