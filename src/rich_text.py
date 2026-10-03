"""Restricted Markdown and native MathML, rendered before the page goes offline."""
import html
from html.parser import HTMLParser
from xml.etree import ElementTree as ET

from latex2mathml.converter import convert
from markdown_it import MarkdownIt
from mdit_py_plugins.dollarmath import dollarmath_plugin


MATH_TAGS = frozenset("math mrow mi mn mo mtext mspace mfrac msqrt mroot msub msup msubsup mover munder munderover mtable mtr mtd menclose mpadded mphantom mstyle mmultiscripts mprescripts none".split())
MATH_ATTRS = frozenset("display mathvariant stretchy fence separator accent accentunder form lspace rspace columnalign rowalign columnspacing rowspacing columnspan rowspan linethickness notation width height depth voffset scriptlevel displaystyle".split())


def math(source: str, display: bool = False) -> str:
    """Only allow inert presentation MathML; unsupported input stays readable."""
    try:
        root = ET.fromstring(convert(source, display="block" if display else "inline"))

        def serialize(node):
            tag = node.tag.rsplit("}", 1)[-1]
            if tag not in MATH_TAGS:
                raise ValueError("Unsupported MathML element")
            attrs = "".join(f' {key}="{html.escape(value, quote=True)}"'
                            for key, value in node.attrib.items() if key in MATH_ATTRS)
            if tag == "math":
                attrs += ' xmlns="http://www.w3.org/1998/Math/MathML"'
            body = html.escape(node.text or "") + "".join(
                serialize(child) + html.escape(child.tail or "") for child in node)
            return f"<{tag}{attrs}>{body}</{tag}>"

        return serialize(root)
    except Exception:
        # A malformed display formula must not prevent rendering the lesson.
        return f'<code class="math-fallback">{html.escape(source)}</code>'


_markdown = MarkdownIt("commonmark", {"html": False}).disable([
    "image", "heading", "lheading", "hr",
]).use(dollarmath_plugin, allow_labels=False, allow_space=False,
       allow_digits=False, renderer=lambda source, options: math(source, options["display_mode"]))


def prose(value: object) -> str:
    return '<div class="rich-text">' + _markdown.render(str(value)) + '</div>'


def inline(value: object) -> str:
    return _markdown.renderInline(str(value))


def plain(value: object) -> str:
    """Readable names for browser titles and accessibility, without Markdown syntax."""
    class Text(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.parts = []

        def handle_data(self, data):
            self.parts.append(data)

    parser = Text()
    parser.feed(inline(value))
    return "".join(parser.parts)


def equation(value: object) -> str:
    source = str(value).strip()
    for left, right in (("$$", "$$"), ("$", "$"), (r"\[", r"\]"), (r"\(", r"\)")):
        if source.startswith(left) and source.endswith(right):
            return math(source[len(left):-len(right)], display=True)
    # Legacy specs use DSL-like equations. Preserve these verbatim rather than
    # guessing a scientific translation. New equations use LaTeX commands.
    if "\\" in source:
        return math(source, display=True)
    return '<code>' + html.escape(source) + '</code>'
