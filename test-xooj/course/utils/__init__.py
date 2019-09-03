# -*- coding: utf-8 -*-
import os
import uuid

from django.conf import settings

from cStringIO import StringIO
from PyPDF2 import PdfFileWriter, PdfFileReader

from reportlab.pdfgen import canvas
from reportlab.lib.units import cm


def create_watermark(full_water_name, content):
    # 默认大小为21cm*29.7cm
    c = canvas.Canvas(full_water_name, pagesize=(30 * cm, 30 * cm))
    # 移动坐标原点(坐标系左下为(0,0))
    c.translate(3 * cm, 5 * cm)

    # 设置字体
    c.setFont("Helvetica", 40)
    # 指定描边的颜色
    c.setStrokeColorRGB(0, 1, 0)
    # 指定填充颜色
    c.setFillColorRGB(0, 1, 0)

    # 旋转45度，坐标系被旋转
    c.rotate(30)
    # 指定填充颜色
    c.setFillColorRGB(0.6, 0, 0)
    # 设置透明度，1为不透明
    c.setFillAlpha(0.3)
    # 画几个文本，注意坐标系旋转的影响
    c.drawString(3 * cm, 0 * cm, content)
    c.drawString(3 * cm, 10 * cm, content)
    c.drawString(3 * cm, 20 * cm, content)

    # 关闭并保存pdf文件
    c.save()


# 所有路径为绝对路径
def add_watermark(pdf_file_in, pdf_file_mark):
    pdf_output = PdfFileWriter()
    BytesIO = StringIO
    pdf_input = PdfFileReader(BytesIO(pdf_file_in), strict=False)
    pdf_watermark = PdfFileReader(file(pdf_file_mark, 'rb'), strict=False)
    watermark = pdf_watermark.getPage(0)

    # 获取PDF文件的页数
    pageNum = pdf_input.getNumPages()
    # 给每一页打水印
    for i in xrange(pageNum):
        page = pdf_input.getPage(i)
        page.mergePage(watermark)
        # page.compressContentStreams()  # 压缩内容
        pdf_output.addPage(page)

    upload_path = os.path.join(settings.MEDIA_ROOT, 'tmp')
    if not os.path.exists(upload_path):
        os.mkdir(upload_path)
    full_pdf_file_name = os.path.join(upload_path, str(uuid.uuid4()) + '.' + 'pdf')

    with open(full_pdf_file_name, "wb") as outputStream:
        pdf_output.write(outputStream)
    return full_pdf_file_name
