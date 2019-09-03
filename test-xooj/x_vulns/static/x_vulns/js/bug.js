/*
 * @Author: Marte
 * @Date:   2017-06-21 15:28:01
 * @Last Modified by:   Marte
 * @Last Modified time: 2017-06-21 16:02:21
 */

'use strict';
$(document).ready(function () {
    $('#table').bootstrapTable({
        dataType: "json",
        toolbar: '#toolbar',                //工具按钮用哪个容器
        striped: false,                      //是否显示行间隔色
        pagination: true, //分页
        pageNumber: 1, //初始化加载第一页，默认第一页
        class: '',
        search: false, //显示搜索框
        onClickRow: function (row) {
            window.location.href = "/x_vulns/detail";
        },
        sidePagination: "client", //服务端处理分页
        columns: [{
            field: '编号',
            title: '编号'
        }, {
            field: '标题',
            title: '标题'
        }, {
            field: '发布时间',
            title: '发布时间'
        }],
        data: [{
            编号: '<a href="javaScript:void(0)">CNNVD-201408-383</a>',
            标题: 'Innovaphone PBX 跨站请求伪造漏洞...',
            发布时间: '2014-08-26 08:00:00'
        }, {
            编号: '<a href="javaScript:void(0)">CNNVD-201408-026</a>',
            标题: 'VMTurbo Operations Manager 代码注入漏洞...',
            发布时间: '2014-08-26 08:00:00'
        }, {
            编号: '<a href="javaScript:void(0)">CNNVD-201407-639</a>',
            标题: 'Innovaphone PBX 跨站请求伪造漏洞...',
            发布时间: '2014-08-26 08:00:00'
        }, {
            编号: '<a href="javaScript:void(0)">CNNVD-201408-383</a>',
            标题: 'Microsoft Windows XP SP3 安全漏洞...',
            发布时间: '2014-08-26 08:00:00'
        }, {
            编号: '<a href="javaScript:void(0)">CNNVD-201407-488</a>',
            标题: 'Linux kernel 权限许可和访问控制漏洞...',
            发布时间: '2014-08-26 08:00:00'
        }, {
            编号: '<a href="javaScript:void(0)">CNNVD-201406-526</a>',
            标题: 'Linux kernel 权限许可和访问控制漏洞...',
            发布时间: '2014-08-26 08:00:00'
        }, {
            编号: '<a href="javaScript:void(0)">CNNVD-201312-186</a>',
            标题: 'Microsoft Internet Explorer 特权提升漏洞...',
            发布时间: '2014-08-26 08:00:00',
        }, {
            编号: '<a href="javaScript:void(0)">CNNVD-201408-383</a>',
            标题: 'Innovaphone PBX 跨站请求伪造漏洞...',
            发布时间: '2014-08-26 08:00:00'
        }, {
            编号: '<a href="javaScript:void(0)">CNNVD-201408-383</a>',
            标题: 'Innovaphone PBX 跨站请求伪造漏洞...',
            发布时间: '2014-08-26 08:00:00'
        }, {
            编号: '<a href="javaScript:void(0)">CNNVD-201408-383</a>',
            标题: 'Innovaphone PBX 跨站请求伪造漏洞...',
            发布时间: '2014-08-26 08:00:00'
        }, {
            编号: '<a href="javaScript:void(0)">CNNVD-201408-383</a>',
            标题: 'Innovaphone PBX 跨站请求伪造漏洞...',
            发布时间: '2014-08-26 08:00:00'
        }, {
            编号: '<a href="javaScript:void(0)">CNNVD-201408-383</a>',
            标题: 'Innovaphone PBX 跨站请求伪造漏洞...',
            发布时间: '2014-08-26 08:00:00'
        }, {
            编号: '<a href="javaScript:void(0)">CNNVD-201408-383</a>',
            标题: 'Innovaphone PBX 跨站请求伪造漏洞...',
            发布时间: '2014-08-26 08:00:00'
        }
        ]
    });
})
