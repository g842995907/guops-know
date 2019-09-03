$(document).ready(function () {
    var bg = document.getElementsByClassName('bg')[0];
    var bgWrap = document.getElementsByClassName('bg-wrap')[0];
    var blackBg = document.getElementsByClassName('black-bg')[0];
    var pull = document.getElementsByClassName('pull')[0];
    var directoryList = document.getElementsByClassName('directory-list');
    var appear = document.getElementsByClassName('appear')[0];
    var courseDetailed = document.getElementsByClassName('course-detailed')[0];
    var doc = document.getElementsByClassName('doc');
    var inportantMain = document.getElementsByClassName('inportant-main');
    var actionBtnList = document.getElementsByClassName('action-btn')[0].getElementsByTagName('li');
    var studyMain = document.getElementsByClassName('study-main')[0];
    var p = studyMain.getElementsByClassName('doc')[0];
    var learnContent = document.getElementsByClassName('learn-content')[0];
    var titleList = document.getElementsByClassName('title-list');
    var listIco = document.getElementsByClassName('list-ico');
    var listText = document.getElementsByClassName('listText');
    var leartTitle = document.getElementsByClassName('learn-title')[0];
    var fourDiv = learnContent.children;
    var right = courseDetailed.offsetWidth - pull.offsetWidth;
    courseDetailed.style.right = '-' + right + 'px'
    listText[0].style.color = 'white';
    listIco[0].style.background = 'white';
    // $('.assess-content>li').click(function(){
    // 	$(this).children('ul').toggle(300);
    // })
    appear.onclick = function () {
        mtween(courseDetailed, 'right', 0, 500, 'linear');
        pull.style.transform = 'rotate(180deg)'
        onOff = false;
    }
    var onOff = true;
    pull.onclick = function () {
        if (onOff) {
            mtween(courseDetailed, 'right', 0, 500, 'linear');
            // this.style.transform='rotate(180deg)'
            onOff = false;
        } else {
            mtween(courseDetailed, 'right', '-' + right, 500, 'linear');
            onOff = true;
            // this.style.transform='rotate(0deg)'
        }

    }
    window.onresize = function () {
        learnContent.style.height = document.documentElement.clientHeight - leartTitle.offsetHeight + 'px';
    }
    learnContent.style.height = document.documentElement.clientHeight - leartTitle.offsetHeight + 'px';
    var docW = document.documentElement.clientWidth;
    // 功能初始化
    var arr = [0];
    actionBtnList[0].className = 'active';
    inportantMain[0].className = 'inportant-main show';
    for (var i = 0; i < actionBtnList.length; i++) {
        actionBtnList[i].status;
        actionBtnList[i].onOff = true;
        actionBtnList[i].index = i;
        actionBtnList[i].onclick = function () {
            // 当点击的是第一个按钮时，修改开关并且生成自定义属性
            if (this.status == undefined && this.index == 0) {
                this.onOff = false;
                this.status = 'go';
            }
            if (this.onOff) {
                // 因为只能有2个按钮为active,所以当arr的长度小于1的时候添加
                if (arr.length <= 1) {
                    arr.push(this.index);
                } else {
                    // 大于1的时候删除数组的第一个，然后再添加到末尾一个，以此循环。
                    arr.shift();
                    arr.push(this.index);
                }
                // 清空一下所有list的class
                for (var i = 0; i < actionBtnList.length; i++) {
                    actionBtnList[i].className = '';
                    actionBtnList[i].onOff = true;
                    actionBtnList[i].status = 'go';
                    fourDiv[i].style.width = '100%';
                    fourDiv[i].style.margin = '0';
                    fourDiv[i].className = 'inportant-main';
                }
                //以数组的内容为下标给actionBtnList添加active,并且修改开关;
                actionBtnList[arr[0]].className = 'active';
                actionBtnList[arr[0]].nextElementSibling.style.display = "none"
                actionBtnList[arr[1]].className = 'active';
                actionBtnList[arr[1]].nextElementSibling.style.display = "none"
                actionBtnList[arr[0]].onOff = false;
                actionBtnList[arr[1]].onOff = false;
                fourDiv[arr[0]].style.width = '50%';
                fourDiv[arr[1]].style.width = '50%';
                fourDiv[arr[0]].className = 'inportant-main show';
                fourDiv[arr[1]].className = 'inportant-main show';
                fourDiv[arr[0]].style.transform = 'translateX(0)';
                fourDiv[arr[1]].style.transform = 'translateX(' + (docW / 2 - 13) + 'px)';
                fourDiv[arr[0]].style.margin = '0';
                fourDiv[arr[1]].style.margin = '0 0 0 -2.7%';

                $.each([fourDiv[arr[0]], fourDiv[arr[1]]], function (i, main) {
                    var $iframe = $(main).find('iframe');
                    if ($iframe.length == 1) {
                        var asyncSrc = $iframe.attr('async-src');
                        if (asyncSrc) {
                            $iframe.attr('src', asyncSrc).removeAttr('async-src');
                        }
                    }
                });

            } else {
                //重复点击同一个按钮去掉class;
                //如果arr的leng为1，表示只有一个按钮高亮了，再点击自己就不去掉高亮了。
                if (arr.length !== 1) {
                    this.className = '';
                    this.nextElementSibling.style.display = "block"
                    // 循环arr，看点击的是哪个，并且把对应arr里的下标删掉。
                    if (this.index == arr[0]) {
                        arr.shift();
                    } else {
                        arr.pop();
                    }
                    this.onOff = true;
                    for (var i = 0; i < fourDiv.length; i++) {
                        fourDiv[i].style.width = '100%';
                        fourDiv[i].className = 'inportant-main';
                    }
                    fourDiv[arr[0]].className = 'inportant-main show';
                    fourDiv[arr[0]].style.margin = '0';
                    fourDiv[arr[0]].style.transform = 'translateX(0)';
                }

            }

        }
    }


    /*滚动条功能*/

    function changeScroll() {
        var HH = rollBody.offsetHeight / (p.offsetHeight / studyMain.offsetHeight);
        if (studyMain.offsetHeight / p.offsetHeight > 1) {
            HH = 0;
            roll.style.display = 'none'
        } else if (studyMain.offsetHeight / p.offsetHeight < 0.1) {
            HH = 20;
            roll.style.display = 'block'
        }
        if (studyMain.offsetHeight / p.offsetHeight < 1) {
            rollBody.addEventListener('DOMMouseScroll', fn, false);
            rollBody.addEventListener('mousewheel', fn, false);
            studyMain.addEventListener('DOMMouseScroll', fn, false);
            studyMain.addEventListener('mousewheel', fn, false);


        }

        rollBtn.style.height = HH + 'px';
        rollBtn.onmousedown = function (e) {
            var boxHeight = rollBody.offsetHeight;
            var box2Height = rollBtn.offsetHeight;
            var pHeight = p.offsetHeight;
            var beginM = e.clientY - rollBtn.offsetTop;
            document.onmousemove = function (e) {
                var box2Top = rollBtn.offsetTop;
                var T = e.clientY - beginM;
                if (T < 0) {
                    T = 0;
                } else if (T > boxHeight - box2Height) {
                    T = boxHeight - box2Height;
                }
                rollBtn.style.top = T + 'px';
                p.style.top = box2Top / (boxHeight - box2Height) * (studyMain.clientHeight - p.offsetHeight) + 'px';
            }
            document.onmouseup = function () {
                document.onmousemove = null;
            }
            return false;
        }
        var state = true;
        rollBottom.onclick = function () {
            state = false;
            place(state);
        }
        rollTop.onclick = function () {
            state = true;
            place(state);
        }
        function fn(e) {
            var onOff = true;
            if (e.wheelDelta) {
                if (e.wheelDelta > 0) {
                    onOff = true;
                } else {
                    onOff = false;
                }
            }
            if (e.detail) {
                if (e.detail > 0) {
                    onOff = false;
                } else {
                    onOff = true;
                }
            }
            place(onOff);
        }

        function place(onOff) {
            var T;
            if (onOff) {
                T = rollBtn.offsetTop - 10;
            } else {
                T = rollBtn.offsetTop + 10;
            }
            if (T < 0) {
                T = 0;
            } else if (T > rollBody.offsetHeight - rollBtn.offsetHeight) {
                T = rollBody.offsetHeight - rollBtn.offsetHeight;
            }
            rollBtn.style.top = T + 'px';
            p.style.top = rollBtn.offsetTop / (rollBody.offsetHeight - rollBtn.offsetHeight) * (rollBody.clientHeight - p.offsetHeight) + 'px';
            return false;

        }
    }

})
