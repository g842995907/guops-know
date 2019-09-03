$(document).ready(function(){
	var bg = document.getElementsByClassName('bg')[0];
    // var bgWrap = document.getElementsByClassName('bg-wrap')[0];
    // var blackBg = document.getElementsByClassName('black-bg')[0];
	// // var pull = document.getElementsByClassName('pull')[0];
	// var directoryList = document.getElementsByClassName('directory-list');
	// var appear = document.getElementsByClassName('appear')[0];
	var courseDetailed = document.getElementsByClassName('course-detailed')[0];
	var doc = document.getElementsByClassName('doc');
	var inportantMain = document.getElementsByClassName('inportant-main');
	var actionBtnList = document.getElementsByClassName('action-btn')[0].getElementsByTagName('li');
    var studyMain = document.getElementsByClassName('study-main')[0];
    var p = studyMain.getElementsByClassName('doc')[0];
    var learnContent = document.getElementsByClassName('learn-content')[0];
    // var titleList = document.getElementsByClassName('title-list');
    // var listIco = document.getElementsByClassName('list-ico');
    // var listText = document.getElementsByClassName('listText');
    var leartTitle = document.getElementsByClassName('learn-title')[0];
    var fourDiv = learnContent.children;
    var right = courseDetailed.offsetWidth;
    courseDetailed.style.right='-'+right+'px';
	var onOff=true;
	// pull.onclick=function(){
	// 	if(onOff){
	// 		mtween(courseDetailed,'right',0,500,'linear');
	// 		this.style.transform='rotate(180deg)';
	// 		onOff=false;
	// 	}else{
	// 		mtween(courseDetailed,'right','-'+right,500,'linear');
	// 		onOff=true;
	// 		this.style.transform='rotate(0deg)'
	// 	}
    //
	// }
	window.onresize=function(){
		learnContent.style.height=document.documentElement.clientHeight - leartTitle.offsetHeight +'px';
	};
	learnContent.style.height=document.documentElement.clientHeight - leartTitle.offsetHeight +'px';

	var docW = document.documentElement.clientWidth;
	// 功能初始化
	var arr=[0];
	actionBtnList[0].className='active';
	inportantMain[0].className='inportant-main show';
	for(var i=0;i<actionBtnList.length;i++){
		actionBtnList[i].status;
		actionBtnList[i].onOff=true;
		actionBtnList[i].index=i;
		actionBtnList[i].onclick=function(){
			// 当点击的是第一个按钮时，修改开关并且生成自定义属性
			if(this.status==undefined&&this.index==0){
				this.onOff=false;
				this.status='go';
			}
			if(this.onOff){
				// 因为只能有2个按钮为active,所以当arr的长度小于1的时候添加
				if(arr.length<=1){
					arr.push(this.index);
				}else{
					// 大于1的时候删除数组的第一个，然后再添加到末尾一个，以此循环。
					arr.shift()
					arr.push(this.index);
				}
				// 清空一下所有list的class
				for(var i=0;i<actionBtnList.length;i++){
					actionBtnList[i].className='';
					actionBtnList[i].onOff=true;
					actionBtnList[i].status='go';
					fourDiv[i].style.width='100%';
					fourDiv[i].className='inportant-main';
				}
					//以数组的内容为下标给actionBtnList添加active,并且修改开关;
		 			actionBtnList[arr[0]].className='active';
		 			actionBtnList[arr[1]].className='active';
		 			actionBtnList[arr[0]].onOff=false;
		 			actionBtnList[arr[1]].onOff=false;
		 			fourDiv[arr[0]].style.width='50%';
		 			fourDiv[arr[1]].style.width='50%';
		 			fourDiv[arr[0]].className='inportant-main show';
		 			fourDiv[arr[1]].className='inportant-main show';
		 			fourDiv[arr[0]].style.transform='translateX(0)';
		 			fourDiv[arr[1]].style.transform='translateX('+(docW/2-13)+'px)';

			}else{
				//重复点击同一个按钮去掉class;
				//如果arr的leng为1，表示只有一个按钮高亮了，再点击自己就不去掉高亮了。
				if(arr.length!==1){
					this.className='';
					// 循环arr，看点击的是哪个，并且把对应arr里的下标删掉。
		 			if(this.index==arr[0]){
		 				arr.shift();
		 			}else{
						arr.pop();
		 			}
		 			this.onOff=true;
		 			for(var i=0;i<fourDiv.length;i++){
		 				fourDiv[i].style.width='100%';
		 				fourDiv[i].className='inportant-main';
		 			}
		 			fourDiv[arr[0]].className='inportant-main show';
		 			fourDiv[arr[0]].style.transform='translateX(0)';
				}

			}

		}
	}
});
