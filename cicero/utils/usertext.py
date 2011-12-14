# -*- coding:utf-8 -*-
import re

from django.utils.html import escape
from html5lib import HTMLParser, serializer, treewalkers

WWW_PATTERN = re.compile(r'(^|\s|\(|\[|\<|\:)www\.', re.UNICODE)
FTP_PATTERN = re.compile(r'(^|\s|\(|\[|\<|\:)ftp\.', re.UNICODE)
PROTOCOL_PATTERN = re.compile(r'(http://|ftp://|mailto:|https://)(.*?)([\.\,\?\!\)]*?)(\s|&gt;|&lt;|&quot;|$)')

_parser = HTMLParser()
_parse = _parser.parseFragment
_serializer = serializer.HTMLSerializer()
_tree_walker = treewalkers.getTreeWalker('simpletree')
_serialize = lambda doc: u''.join(_serializer.serialize(_tree_walker(doc))) if doc.childNodes else u''

def usertext(value):
    doc = _parse(value)

    def urlify(s):
        s = re.sub(WWW_PATTERN, r'\1http://www.', s)
        s = re.sub(FTP_PATTERN, r'\1ftp://ftp.', s)
        s = re.sub(PROTOCOL_PATTERN, r'<a href="\1\2">\1\2</a>\3\4', s)
        return s

    def has_parents(node, tags):
        if node is None:
            return False
        return node.name in tags or has_parents(node.parent, tags)

    text_nodes = [n for n in doc if n.type == 4]
    for node in text_nodes:
        if not has_parents(node, [u'code']):
            node.value = re.sub(ur'\B--\B', u'—', node.value)
        if not has_parents(node, [u'a', u'code']):
            for child in _parse(urlify(escape(node.value))).childNodes:
               node.parent.insertBefore(child, node)
            node.parent.removeChild(node)

    def unjavascript(node):
        for name, attr in [(u'a', u'href'), (u'img', u'src')]:
            if node.name == name and node.attributes.get(attr, '').startswith('javascript:'):
                node.attributes[attr] = ''

    for node in doc:
        unjavascript(node)
        if node.name == u'a':
            node.attributes['rel'] = (node.attributes.get('rel', '') + ' nofollow').strip()

    return _serialize(doc)
