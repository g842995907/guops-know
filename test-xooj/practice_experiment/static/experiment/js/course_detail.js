
$(document).ready(function(){
    var n = window.location.href.split('#')[1];
    var modalType = document.getElementById('modalType');
    // var addNote = document.getElementById('addNote');
    var talk = document.getElementById('talk');
    var modalBody = document.getElementsByClassName('modal-body')[0]
    var commentText = document.getElementsByClassName('commentText');
    var hf = document.getElementsByClassName('hf');
    var cancel = document.getElementsByClassName('cancel');
    var reply = document.getElementsByClassName('reply');
    var talkNum = document.getElementsByClassName('talkNum');

    for(var i=0;i<talkNum.length;i++){
        talkNum[i].onOff=true;
        talkNum[i].onclick=function(){
            if(this.onOff){
                var zNum = this.innerHTML;
                zNum++;
                this.innerHTML = zNum;
                $('.addOne2').eq(i).css('animation','0.5s add linear alternate');
                $(this).addClass('orangeC2');
                setTimeout(function(){
                    $('.addOne2').eq(i).css('animation','');
                },500)
                this.onOff=false;
            }else{
                $('.aleadyZan2').eq(i).css('animation','0.5s add linear alternate');
                setTimeout(function(){
                    $('.aleadyZan2').eq(i).css('animation','');
                },500)
            }

        }
    }
    $('.collectButton').on('click',function(){
        $('i').removeClass('whiteC');
    })
    //点击回复出现评论框
    for(var i=0;i<hf.length;i++){
        hf[i].onclick=function(){
            reply[i].style.display='block';
        }
    }
    for(var i=0;i<cancel.length;i++){
        cancel[i].onclick=function(){
            reply[i].style.display='none';
        }
    }
    //tab点击
    // $('.assess-content>li').click(function(){
    //     $(this).children('ul').toggle(300);
    // })

    $('.commentGo').on('click',function(){
        $(this).parent().parent().next().removeClass("hidden");
    })

    $('.comBtn').on('click',function(){
        var conStr = $(this).prev().val();
        $(this).parent().addClass('hidden');
        var div = document.createElement('div');
        div.className='row pad5A'
        var span = document.createElement('span');
        span.innerHTML = conStr;
        span.className = 'col-md-10 fl orangeC';
        div.appendChild(span);
        $(this).parent().parent().append(div);


    })
})

