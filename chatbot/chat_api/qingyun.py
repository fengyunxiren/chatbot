#!/usr/bin/python3

from chatbot.url_method.url_requests import url_requests
import logging
log = logging.getLogger(__name__)

URL = 'http://api.qingyunke.com/api.php'

def chat(message):
    params = {
            'key': 'free',
            'appid': 0,
            'msg': message,
            }
    resp = url_requests('get', url=URL,
                        params=params, jsonfmt=True)
    if not resp:
        log.error("Chat with 'qingyunke' error!")
        return ''
    if resp['result'] != 0:
        log.error("'Qingyunke' cant understand message(%s).", message)
        return ''
    content = resp['content']
    return content.replace('{br}', '\n')

if __name__ == '__main__':
    print(chat("笑话"))
