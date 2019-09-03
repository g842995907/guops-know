$(document).ready(function () {
    //顶部动画
    // $('.top-wrap').on('mouseenter', function () {
    //     $(this).find('.network-top').stop().slideDown(200)
    // })
    // $('.top-wrap').on('mouseleave', function () {
    //     $(this).find('.network-top').stop().delay(2000).slideUp(300)
    // })

    $('.action-btn li').hover(function () {
        var currentWidth = $(this).find('.action-btn-text').width();
        $(this).find('.action-btn-text ').animate({
            left: -currentWidth - 20,
            opacity: '1'
        }, "slow");
    }, function () {
        var currentWidth = $(this).find('.action-btn-text ').width();
        $(this).find('.action-btn-text ').animate({
            left: currentWidth + 20 ,
            opacity: '0'
        }, "slow");
    });

    //快捷键
    $('.shortcut-icon').click(function () {
        if ($('.shortcut-list').is(':hidden')) {
            $('.shortcut-list').show();
        } else {
            $('.shortcut-list').hide();
        }

    });
    $('.shortcut-list li').on('click', function () {
        $(this).addClass('active').siblings().removeClass('active')
    });

    //  操作按钮位置
    // var actionHeight = $('.action-btn-wrapper').height();
    // $('.action-btn-wrapper').css('marginTop', -actionHeight);

    //隐藏显示目录
    $('.catalog').click(function () {
        $('.catalog-list').slideToggle("slow");

    });
    // $('.catalog-list li').on('click', function () {
    //     $(this).addClass('active').siblings().removeClass('active')
    // });


//    tab切换
    var FirstIframeHeight = true;
    $('.action-btn > li').on('click', function () {
        if($(this).attr('media-name') == 'attachment'){
            return
        }
        var index = $(this).index();
        $(this).addClass('active').siblings().removeClass('active');
        $('.action-btn-wrapper').animate({
            right: '-128px',
        });
        $('.tab-content ').eq(index).css('display', 'block').siblings().css('display', 'none');
        $('.tab-title > li').eq(index).addClass('active').siblings().removeClass('active');
        $('#drag').show('slow', function () {
            if (FirstIframeHeight && index === 0) {
                setIframeHeight(document.getElementById("md_pdf"));
            }
        });

    });

    $('.tab-title > li').on('click', function () {
        var index = $(this).index();
        $(this).addClass('active').siblings().removeClass('active');
        $('.tab-content ').eq(index).show('slow', function () {
            if (FirstIframeHeight && index === 0) {
                setIframeHeight(document.getElementById("md_pdf"));
            }
        }).siblings().hide('fast');
        $('.action-btn > li').eq(index).addClass('active').siblings().removeClass('active');
    });

    $('.catalog-list > li').on('click', function () {
        var index = $(this).index();
        // $(this).addClass('active').siblings().removeClass('active');
        $('.tab-content ').eq(index).show('slow').siblings().hide('fast');
        $('.tab-title > li').eq(index).addClass('active').siblings().removeClass('active');
    });
//    关闭弹框 显示操作按钮
    $('.tab-wrap .close-tab').on('click', function () {
        $('.action-btn-wrapper').animate({
            right: '0',
        });
        $('#drag').hide('slow');
    })

    $('.env-head .close-tab').on('click', function () {
        $('.env').hide('slow');
    })
//    查看拓扑弹出层
    $('#env-btn').on('click', function () {
        if ($('.env').is(':hidden')) {
            $('.env').show('slow', function () {
                var network = envWidget.getInstance($('[data-widget-id=common-env]')).network;
                network.redraw();
                network.fit();
            });
        } else {
            $('.env').hide('slow');
        }
    });
    $('#clipboard-modal').on('click', function () {
        if ($('.clipboard').is(':hidden')) {
            $('.clipboard').show('show');
        } else {
            $('.clipboard').hide('slow');
        }
    })
})

