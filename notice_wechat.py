def notice_me(op_type="交易", text=""):
    # 推送量化交易信息给自己！
    import requests
    url = "https://new.dottmed.com/wechat/wechat_notice/"

    payload = {
        'op_type': op_type,
        'text': text,
        'openid': 'oUeNB6ILXAtcU5JNqKBUXFZyBkyQ'
    }

    response = requests.request("POST", url, data=payload,timeout=3)