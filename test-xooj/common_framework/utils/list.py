# -*- coding: utf-8 -*-

def convert_item(stype, item):
    if isinstance(item, str) and stype == unicode:
        return unicode(item, 'utf-8')
    return stype(item)

def typefilter(slist, stype):
    rlist = []
    for item in slist:
        if item:
            try:
                rlist.append(convert_item(stype, item))
            except:
                continue
    return rlist

def areafilter(slist, sarea):
    stype = type(sarea[0])
    rlist = typefilter(slist, stype)
    return list(set(sarea) & set(rlist))

def listfilter(slist, param):
    if isinstance(param, (tuple, list, set)):
        return areafilter(slist, param)

    return typefilter(slist, param)

def valuefilter(value, param):
    ret = listfilter([value], param)
    if ret:
        return ret[0]
    return None

