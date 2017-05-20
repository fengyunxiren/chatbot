#!/usr/bin/python3

from chatbot.url_method.url_requests import url_requests
import json
import logging
log = logging.getLogger(__name__)

URL = 'http://www.tuling123.com/openapi/api'
APIKEY = '75af9f7554ae497b80ec26308e5e46ac'

def chat(message, userid='123456789', local=None):
    params = {
            'key': APIKEY,
            'userid': userid,
            'info': message,
            }
    if local is not None:
        params['loc'] = local
    try:
        resp = url_requests('get', url=URL,
                        params=params, jsonfmt=True)
    except Exception as ex:
        log.error("Request 'tuling':%s", ex)
        return ''
    if not resp:
        log.error("Chat with 'tuling' error!")
        return ''
    state = resp.pop('code')
    error_state = [40001, 40002, 40004, 40007]
    if state in error_state:
        log.error("Error state: %s", state)
    if state == 100000:
        return resp['text']
    elif state == 200000:
        return ':\n'.join([resp['text'], resp['url']])
    elif state == 302000 or state == 308000:
        return ':\n'.join([resp['text'],
                           json.dumps(resp['list'], ensure_ascii=False)])
    else:
        return json.dumps(resp)


if __name__ == '__main__':
    print(chat("从河东到河西，从荷兰到河北，不知道你说的是啥东东，请问你知道不知道，不能超过长度吗"))
