#!/usr/bin/python3

import requests
import logging
import json
log = logging.getLogger(__name__)

access_method = {
        'GET': requests.get,
        'PUT': requests.put,
        'POST': requests.post,
        'DELETE': requests.delete,
        'HEAD': requests.head,
        }


def url_requests(method='GET', *args, **kwargs):
    if 'jsonfmt' in kwargs:
        jsonfmt = kwargs.pop('jsonfmt')
        if 'data' in kwargs and jsonfmt:
            kwargs['data'] = json.dumps(kwargs['data'], ensure_ascii=False)\
                             .encode('utf-8')
    else:
        jsonfmt = False
    if 'cookies' in kwargs:
        has_cookies = True
    else:
        has_cookies = False

    add_headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36'}

    if 'headers' in kwargs:
        kwargs['headers'].update(add_headers)
    else:
        kwargs['headers'] = add_headers
    method = method.upper()

    try:
        resp = access_method[method](*args, **kwargs)
    except Exception as ex:
        log.error("Error: %s", ex)
        return None

    if resp.status_code < 200 or resp.status_code >=300:
        log.error("Error: %s", resp.reason)
        return None
    resp.encoding = 'utf-8'
    if jsonfmt:
        try:
            if has_cookies and resp.cookies:
                return (resp.json(), resp.cookies)
            elif has_cookies and not resp.cookies:
                return (resp.json(), dict())
            else:
                return resp.json()
        except Exception as ex:
            log.error("Error: %s", ex)
            return None

    if has_cookies and resp.cookies:
        return (resp.text, resp.cookies)
    elif has_cookies and not resp.cookies:
        return (resp.text, dict())
    else:
        return resp.text





if __name__ == '__main__':
    url = 'http://api.qingyunke.com/api.php'
    params = {
            'key': 'free',
            'appid': 0,
            'msg': '你好',
            }
    resp = url_requests('get', url=url, params=params)
    print(resp)
