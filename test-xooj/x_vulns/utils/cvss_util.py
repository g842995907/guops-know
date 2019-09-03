# -*- coding: utf-8 -*-
from django.utils.translation import ugettext as _


def gen_severity(score):
    try:
        score = float(score)
        if score <= 5:
            return {"class": "severity_low", "title": _("x_low_risk"), "level": 1, "style":"yellows"}
        elif score > 5 and score <= 7:
            return {"class": "severity_medium", "title": _("x_medium_risk"), "level": 2, "style":"oranges"}
        elif score > 7:
            return {"class": "severity_high", "title": _("x_high_risk"), "level": 3, "style":"reds"}
        else:
            return {"class": "severity_none", "title": u"暂无数据", "level": -1, "style":"greys"}
    except Exception, e:
        return {"class": "severity_none", "title": u"暂无数据", "level": -1, "style":"greys"}


def gen_cvss_indicator(cvss_data):
    titles = {"score": u'CVSS分值',
              "c": u'机密性影响',
              "i": u'完整性影响',
              "a": u'可用性影响',
              "ac": u'攻击复杂度',
              "av": u'攻击向量',
              "au": u'身份认证'
              }
    if not cvss_data:
        return {"has_data": "0", "title": titles}
    cvss_check = ''.join([cvss_data[k] for k in cvss_data.keys()])
    if not cvss_check:
        return {"has_data": "0", "title": titles}
    raw = {"score": cvss_data.get("score"),
           "av": cvss_data.get("access-vector"),
           "ac": cvss_data.get("access-complexity"),
           "au": cvss_data.get("authentication") or 'NONE',
           "c": cvss_data.get("confidentiality-impact") or 'NONE',
           "i": cvss_data.get("integrity-impact") or 'NONE',
           "a": cvss_data.get("availability-impact") or 'NONE'
           }
    impacts = {"NONE": (0, u"green", u"无"),
               "PARTIAL": (1, u"oranges", u"部分"),
               "COMPLETE": (2, u"reds", u"完全")}
    acess_vectors = {"LOCAL": (0, u"yellows", u"本地"),
                     "ADJACENT_NETWORK": (1, u"oranges", u"ADJA——Network"),
                     "NETWORK": (2, u"reds", u"网络")}
    access_complexities = {"LOW": (0, u"reds", u"低"),
                           "MEDIUM": (1, u"oranges", u"中"),
                           "HIGH": (2, u"yellows", u"高")}
    authentications = {"NONE": (0, u"reds", u"无"),
                       "SINGLE": (1, u"oranges", u"单一"),
                       "MULTIPLE": (2, u"yellows", u"多个"),
                       "SINGLE_INSTANCE": (1, u"oranges", u"单一"),}
    vals = {}
    for k in raw:
        k_c = raw.get(k, '')
        if not k_c: k_c = ''
        if k == "score":
            vals[k] = raw.get(k, '')
        elif k in ['c', 'i', 'a']:
            vals[k] = impacts.get(k_c.upper(), '')
        elif k == "av":
            vals[k] = acess_vectors.get(k_c.upper(), '')
        elif k == "ac":
            vals[k] = access_complexities.get(k_c.upper(), '')
        elif k == "au":
            vals[k] = authentications.get(k_c.upper(), '')
    severity = gen_severity(cvss_data.get('score'))
    indicator = {"has_data": "1", "title": titles, "value": vals, "severity": severity}
    return indicator