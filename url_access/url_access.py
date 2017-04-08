#!/usr/bin/python3

from urllib import request

def get_url_data(url, headers=None, body=None, jsonfmt=False):
    """
    Get data from url.
    param: str url: a access url.
    param: dict headers: a dict that need add to url header, used in get method.
    param: dict body: http post params.
    param: bool jsonfmt: return a json format data if it set True.
    """

