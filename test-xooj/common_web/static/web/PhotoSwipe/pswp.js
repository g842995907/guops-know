var pswpElement = document.querySelectorAll('.pswp')[0];
// build items array
var img = $('.photoswipe img');
img.each(function (index, element) {
    $(this).click(function () {
        var items = [];
        $('.photoswipe img').each(function (index, element) {
            items.push({
                src: element.src,
                w: element.width,
                h: element.height,
            });
        });

        var options = {
            index: index,// start at first slide
            shareEl: false,
        };
        var gallery = new PhotoSwipe(pswpElement, PhotoSwipeUI_Default, items, options);
        gallery.init();
    })
})
