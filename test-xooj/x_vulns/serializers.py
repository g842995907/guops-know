# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from pyquery import PyQuery as pq

from rest_framework import serializers

from x_vulns.models import ExtCvenvd, ExtCnnvd, ExtEdb, ExtNvd


class ExtEdbSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtEdb
        fields = '__all__'


class BaseExtCvenvdSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    product_list = serializers.SerializerMethodField()
    vul_refs = serializers.SerializerMethodField()

    def get_title(self, obj):
        return get_vulns_title(obj)

    def get_product_list(self, obj):
        return obj.products.split('|') if obj.products else []

    def get_vul_refs(self, obj):
        vul_refs = []
        try:
            references = pq(obj.vul_ref)('references')
            for ref in references:
                ref = pq(ref)
                vul_refs.append({
                    'type': ref.attr('reference_type'),
                    'src': ref.find('source').text(),
                    'url': ref.find('reference').attr('href'),
                    'info': ref.find('reference').text(),
                })
        except:
            pass
        return vul_refs

    class Meta:
        model = ExtCvenvd
        fields = '__all__'


class BaseExtCnnvdSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()

    def get_title(self, obj):
        return get_vulns_title(obj)

    class Meta:
        model = ExtCnnvd
        fields = '__all__'


class ExtCvenvdSerializer(BaseExtCvenvdSerializer):
    cnnvd = serializers.SerializerMethodField()
    edb = serializers.SerializerMethodField()

    def get_cnnvd(self, obj):
        cnnvd = ExtCnnvd.objects.filter(ref_cve=obj.id).first()
        if cnnvd:
            return BaseExtCnnvdSerializer(cnnvd).data
        else:
            return None

    def get_edb(self, obj):
        edb = ExtEdb.objects.filter(ref_cve=obj.id).first()
        if edb:
            return ExtEdbSerializer(edb).data
        else:
            return None


class ExtCnnvdSerializer(BaseExtCnnvdSerializer):
    cvenvd = serializers.SerializerMethodField()
    edb = serializers.SerializerMethodField()

    def get_cvenvd(self, obj):
        if obj.ref_cve:
            return BaseExtCvenvdSerializer(obj.ref_cve).data
        else:
            return None

    def get_edb(self, obj):
        if obj.ref_cve:
            edb = ExtEdb.objects.filter(ref_cve=obj.ref_cve.id).first()
            if edb:
                return ExtEdbSerializer(edb).data
            else:
                return None
        else:
            return None


class ExtNvdSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()

    def get_title(self, obj):
        return get_vulns_title(obj)

    class Meta:
        model = ExtNvd
        fields = '__all__'


def get_vulns_title(vulns):
    if vulns.summary:
        return vulns.summary if len(vulns.summary) <= 100 else vulns.summary[0: 100] + '...'
    else:
        return ''