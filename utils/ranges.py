# -*- coding:utf-8 -*-
def merge_range(new_range, ranges):
  '''
  Вливает новый диапазон new_range в список диапазонов ranges
  '''
  def is_intersected(range1, range2):
    return (range1[1] >= range2[0] - 1 and range1[0] <= range2[1] + 1)

  def merge(range1, range2):
    return (min(range1[0], range2[0]), max(range1[1], range2[1]))

  new_ranges=[]
  for range in ranges:
    if is_intersected(new_range, range):
      new_range = merge(new_range, range)
    else:
      new_ranges.append(range)
  new_ranges.append(new_range)
  new_ranges.sort()

  return new_ranges
  
def compile_ranges(ids):
  '''
  Переводит набор чисел в набор непрерывных диапазонов
  '''
  ids.sort()
  left = right = None
  for id in ids:
    if not left:
      left = right = id
    elif id == right + 1:
      right += 1
    else:
      yield (left, right)
      left = right = id
  if left:
    yield (left, right)