(function () {
    function setTcheckBallPosition($jsTcheck, offset) {
        var $ball = $jsTcheck.find('.tcheck-ball');
        var left = 0;
        for (var i = offset; i >0; i--) {
            var $tcheck = $jsTcheck.find('.tcheck[data-offset=' + i + ']');
            var tcheckWith = Number($tcheck.css('width').replace('px', ''));
            left = left + tcheckWith;
        }
        $ball.css('left', left + 'px');
    }

    // 从左往右3个选项代表的select下标
    // left选项代表下标为1的option
    // center选项代表下标为0的option
    // right选项代表下标为2的option
    var optionEqs = [1, 0, 2];

    $.fn.applyTCheck = function (options) {
        options = options || {};
        this.hide();
        this.each(function(i, select){
            $jsTcheck = $(`
                <div class="js-tcheck clearfix">
                    <span class="tcheck pull-left" data-id="tcheck-l" data-offset="0"></span>
                    <span class="tcheck pull-left" data-id="tcheck-c" data-offset="1"></span>
                    <span class="tcheck pull-left" data-id="tcheck-r" data-offset="2"></span>
                    <span class="tcheck-ball" data-on="tcheck-l"></span>
                </div>
            `);
            $jsTcheck.find('.tcheck').click(function () {
                var $ball = $jsTcheck.find('.tcheck-ball');
                var id = $(this).attr('data-id');
                var ballOn = $ball.attr('data-on');
                if (id == ballOn) {
                    return;
                }
                $ball.attr('data-on', id);

                var offset = Number($(this).attr('data-offset'));
                setTcheckBallPosition($jsTcheck, offset);

                var tcheckIndex = $.inArray(this, $jsTcheck.find('.tcheck'));
                var selectedValue = $(select).find('option').eq(optionEqs[tcheckIndex]).val();
                $(select).val(selectedValue);
                $(select).change();
            });
            $(select).after($jsTcheck);

            var selectedOffset = options.offset;
            if (selectedOffset == undefined) {
                var selectedOption = $(select).find('option:selected')[0];
                var selectedOptionEq = $.inArray(selectedOption, $(select).find('option'));
                selectedOptionEq = selectedOptionEq == -1 ? 0 :selectedOptionEq;
                var tcheckIndex = $.inArray(selectedOptionEq, optionEqs);
                selectedOffset = Number($jsTcheck.find('.tcheck').eq(tcheckIndex).attr('data-offset'));
            }
            var initDataOn = $jsTcheck.find('.tcheck[data-offset=' + selectedOffset + ']').attr('data-id');
            $jsTcheck.find('.tcheck-ball').attr('data-on', initDataOn);
            setTcheckBallPosition($jsTcheck, selectedOffset);
        });
    };
}())

