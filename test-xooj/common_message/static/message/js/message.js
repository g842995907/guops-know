$(document).ready(function(){
	var ojMessage = document.getElementsByClassName('oj_message');
	for(var i=0;i<ojMessage.length;i++){
		// popping(posRelative[i]);
		ojMessage[i].index=i;
		ojMessage[i].onmouseover=function(){
			mesHover(this.index,this.children[1],'messInner mesBg2 pad20R','#01f8ff','#cbccce',this.children[1].children[0],'bold')
		}
		ojMessage[i].onmouseout=function(){
			mesHover(this.index,this.children[1],'messInner mesBg1 pad20R','#cbccce','#01f8ff',this.children[1].children[0],'')
		}
	}
	function mesHover(num,who1,classN,color1,color2,who2,what){
		// var span = megCon[num].getElementsByTagName('span');
		who1.className=classN;
		who2.style.color=color2;
		who2.style.fontWeight=what;
	}
})