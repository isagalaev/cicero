# -*- coding:utf-8 -*-
'''
Составление картинки мутанта из отдельных частей
(рук, ног, головы, туловища). Части выбираются на основе OpenID
и составляются в своего персонального уникального мутанта
для каждого пользователя. Используются в качестве прикольной
визуализации OpenID.
'''

import Image
import os

from django.conf import settings

def partfile(part, index):
    path = os.path.join(settings.CICERO_OPENID_MUTANT_PARTS, part)
    files = os.listdir(path)
    files.sort()
    return os.path.join(path, files[ord(index) % len(files)])

def transpose(image, index):
    if ord(index) > 127:
        image = image.transpose(Image.FLIP_LEFT_RIGHT)
    return image

def shadow(image):
    shadow = Image.new('RGBA', (image.size[0] + 4, image.size[1] + 4))
    shadow.paste((0, 0, 0, 180), (1, 1, image.size[0] + 1, image.size[1] + 1), image)
    from ImageEnhance import Sharpness
    shadow = Sharpness(shadow).enhance(0.1)
    shadow = Sharpness(shadow).enhance(0.1)
    shadow = Sharpness(shadow).enhance(0.1)
    shadow.paste(image, (0, 0, image.size[0], image.size[1]), image)
    return shadow

def mutant(openid, openid_server):
    from urlparse import urlsplit
    openid = '%s://%s%s' % urlsplit(openid)[0:3]
    import md5
    hash = md5.new(openid).digest()
    extremities = Image.new('RGBA', (48, 48))
    arms = Image.new('RGBA', (48, 48))
    for filename in (partfile('arm-left', hash[0]), partfile('arm-right', hash[1])):
        image = Image.open(filename).convert('RGBA')
        arms.paste(image, mask=image)
    arms = transpose(arms, hash[2])
    extremities.paste(arms, mask=arms)
    legs = Image.new('RGBA', (48, 48))
    for filename in (partfile('leg-left', hash[3]), partfile('leg-right', hash[4])):
        image = Image.open(filename).convert('RGBA')
        legs.paste(image, mask=image)
    legs = transpose(legs, hash[5])
    extremities.paste(legs, mask=legs)
    head = Image.open(partfile('head', hash[6])).convert('RGBA')
    head = transpose(head, hash[7])
    body = Image.open(partfile('body', hash[8])).convert('RGBA')
    body = transpose(body, hash[9])

    host = urlsplit(openid)[1]
    host = '.'.join(host.split('.')[-2:])
    hash = md5.new(host).digest()
    from ImageOps import colorize
    result = Image.new('RGBA', (48, 48))
    for index, image in enumerate((extremities, body, head)):
        color = settings.CICERO_OPENID_MUTANT_COLORS[ord(hash[index]) % len(settings.CICERO_OPENID_MUTANT_COLORS)]
        colorized = colorize(image.convert('L'), color, (255, 255, 255))
        result.paste(colorized, mask=image)

    result = shadow(result)

    if settings.CICERO_OPENID_MUTANT_BACKGROUND:
        canvas = Image.new('RGB', result.size, settings.CICERO_OPENID_MUTANT_BACKGROUND)
        canvas.paste(result, mask=result)
        result= canvas

    return result
