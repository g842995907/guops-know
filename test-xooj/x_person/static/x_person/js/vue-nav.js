(function(){
var tm = '<div class="page-bar centerDiv">'+
            '<ul>'+
            '<li v-if="cur != 1"><a @click="btnClick(cur-1)">'+gettext("x_pre_page")+ '</a></li>'+
            '<li v-for="index in indexs" v-bind:class="{ active: cur == index}">'+
              '<a v-on:click="btnClick(index)">{{ index }}</a>'+
              '</li>'+
              '<li v-if="cur != all"><a @click="btnClick(cur+1)">'+gettext('x_next_page')+'</a></li>'+
              '<li><a>' + gettext("x_page_num").format({"all": '<i>{{all}}</i>' }) + '</a></li>'+
            '</ul>'+
          '</div>'

var navBar = Vue.extend({
    template: tm,
    props: {
      cur: {
        type: [String, Number],
        required: true
      },
      all: {
        type: [String, Number],
        required: true
      },
      callback: {
        default: function () {
            return function callback() {
                // todo
            }
        },
      },
    },
    computed: {
        indexs: function () {
            var left = 1
            var right = this.all
            var ar = []
            if (this.all >= 11) {
                if (this.cur > 5 && this.cur < this.all - 4) {
                    left = this.cur - 5
                    right = this.cur + 4
                } else {
                    if (this.cur <= 5) {
                        left = 1
                        right = 10
                    } else {
                        right = this.all
                        left = this.all -9
                    }
                }
            }
            while (left <= right) {
                ar.push(left)
                left ++
            }
            return ar
        },
    },
    methods: {
        btnClick: function (page) {
            if (page != this.cur && page != 0 && page != this.all + 1) {
                this.callback(page)
            }
        },
    }
})

window.Vnav = navBar

})()