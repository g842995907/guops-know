# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils import timezone


class ExtBase(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    summary = models.TextField(null=True)
    pub_date = models.DateTimeField(null=True)
    upd_date = models.DateTimeField(null=True)
    plugin_time = models.DateTimeField(null=True)
    plugin_createtime = models.DateTimeField(null=True)
    edit_time = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True


class ExtCvenvd(ExtBase):
    cvss_score = models.FloatField(null=True)
    cvss_acc_vec = models.CharField(max_length=50, null=True)
    cvss_acc_comp = models.CharField(max_length=50, null=True)
    cvss_auth = models.CharField(max_length=50, null=True)
    cvss_conf_imp = models.CharField(max_length=50, null=True)
    cvss_int_imp = models.CharField(max_length=50, null=True)
    cvss_ava_imp = models.CharField(max_length=50, null=True)
    ref_cwe = models.CharField(max_length=50, null=True)
    products = models.TextField(null=True)
    cpe_conf = models.TextField(null=True)
    vul_ref = models.TextField(null=True)
    raw_data = models.TextField(null=True)


class ExtCnnvd(ExtBase):
    severity = models.CharField(max_length=20, null=True)
    type_v = models.CharField(max_length=50, null=True)
    type_t = models.CharField(max_length=50, null=True)
    ref_cve = models.ForeignKey(ExtCvenvd, on_delete=models.PROTECT)
    description = models.TextField(null=True)
    bulletin = models.TextField(null=True)
    plugin_url = models.CharField(max_length=300)


class ExtNvd(models.Model):
    '''
        ExtCvenvd, ExtCnnvd合并表
        insert into custom_admin_extnvd select id, summary, pub_date, edit_time from custom_admin_extcvenvd;
        insert into custom_admin_extnvd select id, summary, pub_date, edit_time from custom_admin_extcnnvd;
    '''
    id = models.CharField(max_length=50, primary_key=True)
    summary = models.TextField(null=True)
    pub_date = models.DateTimeField(null=True)
    edit_time = models.DateTimeField(default=timezone.now)


class ExtEdb(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    v_name = models.CharField(max_length=500, null=True)
    v_platform = models.CharField(max_length=20, null=True)
    v_type = models.CharField(max_length=20, null=True)
    ref_cve = models.CharField(max_length=80, null=True)
    ref_osvdb = models.CharField(max_length=20, null=True)
    v_file = models.CharField(max_length=250, null=True)
    v_port = models.CharField(max_length=10, null=True)
    verify = models.CharField(max_length=20, null=True)
    author = models.CharField(max_length=80, null=True)
    pub_date = models.DateTimeField(null=True)
    exp_code = models.CharField(max_length=80, null=True)
    vuln_app = models.CharField(max_length=80, null=True)
    code_lang = models.CharField(max_length=30, null=True)
    code_content = models.TextField(null=True)
    plugin_time = models.DateTimeField(null=True)
    plugin_url = models.CharField(max_length=300, null=True)
    plugin_createtime = models.DateTimeField(null=True)

