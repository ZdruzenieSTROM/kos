"""Pomocné funkcie pre hromadné emaily"""
import re
from html.parser import HTMLParser

BLOCK_TAGS = {'p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
              'ul', 'ol', 'blockquote', 'pre', 'table', 'tr'}


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.links = []
        self.lists = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'br':
            self.parts.append('\n')
        elif tag in BLOCK_TAGS:
            self.parts.append('\n\n')
            if tag in ('ul', 'ol'):
                self.lists.append([tag, 0])
        elif tag == 'li':
            prefix = '- '
            if self.lists and self.lists[-1][0] == 'ol':
                self.lists[-1][1] += 1
                prefix = f'{self.lists[-1][1]}. '
            self.parts.append('\n' + '  ' * max(len(self.lists) - 1, 0) + prefix)
        elif tag == 'a':
            self.links.append((attrs.get('href'), len(self.parts)))

    def handle_endtag(self, tag):
        if tag in BLOCK_TAGS:
            self.parts.append('\n\n')
            if tag in ('ul', 'ol') and self.lists:
                self.lists.pop()
        elif tag == 'a' and self.links:
            href, start = self.links.pop()
            text = ''.join(self.parts[start:]).strip()
            if href and href not in (text, f'mailto:{text}'):
                self.parts.append(f' ({href})')

    def handle_data(self, data):
        self.parts.append(re.sub(r'\s+', ' ', data))

    def text(self):
        text = ''.join(self.parts)
        text = re.sub(r'[ \t]+\n', '\n', text)
        text = re.sub(r'\n[ \t]+(?=[^-\d ])', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()


def html_to_text(html: str) -> str:
    """Prevedie HTML správu na čistý text (pre klientov bez HTML)"""
    parser = _TextExtractor()
    parser.feed(html)
    parser.close()
    return parser.text()


def wrap_html(body: str) -> str:
    """Zabalí telo správy do kompletného HTML dokumentu"""
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8"></head>'
        '<body style="font-family: Arial, Helvetica, sans-serif; '
        'font-size: 14px; line-height: 1.5;">'
        f'{body}</body></html>'
    )
