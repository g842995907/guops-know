$(document).ready(function () {
    //定位申请环境按钮
    $('.apply-env-action-btn').on('click', function () {
        var markdownFrame = $('iframe[name=pdf]');
        markdownFrame[0].contentDocument.scrollingElement.scrollTop = 0;
        $(this).addClass('active');
        $('ul.action-btn > li').removeClass('active');
        $('.content div.frame-pdf').show("slow");
        $('.content div:not(".frame-pdf")').hide("slow");

    })

    //页面切换
    $('.content > .frame-warp').eq(0).show();
    $('ul.action-btn > li').on('click', function () {
        var index = $(this).index();
        $(this).addClass('active').siblings().removeClass('active');

        if ($(this).attr('media-name') == 'pdf') {
            var markdownFrame = $('iframe[name=pdf]');
            var markdownFrameTitle = markdownFrame.contents().find(".markdown-wrapper  h2 > center");
            if (markdownFrameTitle.length > 0) {
                var mTop = markdownFrameTitle.offset().top;
                if (mTop > 50) {
                    markdownFrame[0].contentDocument.scrollingElement.scrollTop = $('.frame-warp').height();
                }
            }
        }
        $('.apply-env-action-btn').removeClass('active');
        var iframeWarp = $('.content > .frame-warp');
        iframeWarp.eq(index).show("slow").siblings().hide("slow");
    })


})

