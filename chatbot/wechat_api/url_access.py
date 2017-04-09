#!/usr/bin/python3

from urllib import request, parse
import json
import logging
log = logging.getLogger(__name__)

def get_url_data(url, headers=None, body=None, jsonfmt=False):
    """
    Get data from url.
    param: str url: a access url.
    param: dict headers: a dict that need add to url header, used in get method.
    param: dict body: http post params.
    param: bool jsonfmt: return a json format data if it set True.
    """
    if body is not None:
        if jsonfmt:
            data = (json.dumps(body)).encode()
        else:
            data = parse.urlencode(body).encode("utf-8")
    if headers is not None:
        if body is not None:
            req = request.Request(url=url, data=data)
        else:
            req = request.Request(url=url)

        for key, header in headers.items():
            req.add_header(key, header)

    else:
        if body is not None:
            req = request.Request(url=url, data=data)
        else:
            req = request.Request(url=url)

    try:
        with request.urlopen(req) as f:
            response = {}
            data = f.read()
            response['status'] = f.status
            response['reason'] = f.reason
            response['headers'] = {}
            for key, value in f.getheaders():
                response['headers'][key] = value
            if jsonfmt:
                response['data'] = json.loads(data.decode('utf-8'))
            else:
                response['data'] = data.decode('utf-8')
    except Exception as ex:
        log.error("Error: %s", ex)
        return None

    return response

if __name__ == '__main__':
    #url = 'https://login.weixin.qq.com/jslogin'
    url = 'http://www.douban.com/'
    headers = {
            'User-Agent': 'Mozilla/6.0 (iPhone; CPU iPhone OS 8_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/8.0 Mobile/10A5376e Safari/8536.25',
            }
    print(get_url_data(url=url, headers=headers))
