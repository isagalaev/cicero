# -*- coding:utf-8 -*-
namespaces = {
  'atom': 'http://www.w3.org/2005/Atom',
  'app': 'http://www.w3.org/2007/app',
}

try:
  import xml.etree.ElementTree as ET
except ImportError:
  import elementtree.ElementTree as ET

def _fixup_element_prefixes(elem, uri_map, memo, default):
  if elem.tag not in memo:
    uri, tag = elem.tag[1:].split("}")
    memo[elem.tag] = uri_map[uri] == default and tag or uri_map[uri] + ":" + tag
  elem.tag = memo[elem.tag]
  for key, value in elem.items():
    if key.startswith('xmlns:'):
      del elem.attrib[key]

def _set_prefixes(root, default):
  uri_map = dict((uri, prefix) for prefix, uri in namespaces.items())  
  for elem in root.getiterator():
    _fixup_element_prefixes(elem, uri_map, {}, default)
  for prefix, uri in namespaces.items():
    attrib = prefix == default and 'xmlns' or 'xmlns:%s' % prefix
    root.set(attrib, uri)

def _element(prefix, name):
  return ET.Element('{%s}%s' % (namespaces[prefix], name))

def _pretty_print(node, level=0):
  def indent(level):
    return '\n' + '  ' * level
  if node.text or not len(node):
    return
  node.text = indent(level + 1)
  for child in node:
    child.tail = indent(level + 1)
    _pretty_print(child, level + 1)
  child.tail = indent(level)


class Collection(object):
  def __init__(self, title, workspace, href):
    self.title, self.workspace, self.href = title, workspace, href
    self.accept = []
  
  def service_xml(self):
    result = _element('app', 'collection')
    result.attrib['href'] = self.href
    title = _element('atom', 'title')
    title.text = self.title
    result.append(title)
    for mimetype in self.accept:
      element = _element('app', 'accept')
      element.text = mimetype
      result.append(element)
    return result

def service_document(collections):
  root = _element('app', 'service')
  workspaces = {}
  for c in collections:
    if c.workspace not in workspaces:
      workspaces[c.workspace] = []
    workspaces[c.workspace].append(c)
  for workspace, collections in workspaces.items():
    ws_element = _element('app', 'workspace')
    title = _element('atom', 'title')
    title.text = workspace
    ws_element.append(title)
    root.append(ws_element)
    for collection in collections:
      ws_element.append(collection.service_xml())
  _set_prefixes(root, 'app')
  _pretty_print(root)
  return ET.ElementTree(root)

if __name__ == '__main__':
  collections = [
    Collection('collection1', 'workspace1', 'http://localhost/collection1'),
    Collection('collection2', 'workspace2', 'http://localhost/collection2'),
    Collection('collection3', 'workspace1', 'http://localhost/collection3'),
  ]
  collections[0].accept = ['image/jpeg', 'image/png']
  service_document(collections).write('/home/maniac/Desktop/text.xml', encoding='utf-8')