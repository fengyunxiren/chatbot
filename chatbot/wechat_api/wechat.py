#!/usr/bin/python3

import uuid
import logging
import os
import time
import datetime
import re
import qrcode
from xml.dom import minidom
from url_access import get_url_data
import random

log = logging.getLogger(__name__)

import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import http.cookiejar
import requests
import json


class WebWeChat(object):
    def __init__(self, storage_path=None, lang=None):
        self.status = None
        self.uuid = None
        self.login_url = 'https://login.weixin.qq.com'
        self.base_url = None
        self.redirect_uri = None
        self.storage_path = storage_path or os.path.join(os.getcwd(), 'storage')
        self.appid = 'wx782c26e4c19acffb'
        self.lang = lang or 'zh_CN'
        self.retry = 10
        self.interval = 2
        self.timeout = 90
        self.request_parm = {}
        self.pass_ticket = None
        self.skey = None

    def login(self):
        self.status = 'Loging'
        log.info("Start Web WeChat...")
        retry = self.retry
        while (not self.uuid) and self.status == 'Loging':
            log.info("Get QR code...")
            if retry == 0:
                self.status = 'Exit'
                continue
            if not self.get_uuid():
                retry -= 1
                time.sleep(self.interval)
                continue
        log.info("Please use wechat to scan qr code to log in...")
        state = self.show_qr_code()
        if not state:
            self.status = 'LogError'
        if self.status == 'Loging':
            self.status = 'WaitLoging'
        
        time_start = time.time()
        tip = 1
        while self.status == 'WaitLoging':
            if self.wait_login(tip=tip):
                if tip == 0:
                    self.status = 'Loged'
                    continue
                else:
                    tip = 0
                    log.info("Please ensure in wechat to log in...")
            if int(time.time() - time_start) > self.timeout:
                log.error("Error: Too long time to wait for...")
                self.status = 'Timeout'
                continue
            time.sleep(self.interval)
        return self.status == 'Loged'


    def get_uuid(self):
        url = 'https://login.weixin.qq.com/jslogin'
        params = {
                'appid': self.appid,
                'fun': 'new',
                'lang': self.lang,
                '_': int(time.time()),
                }
        response = get_url_data(url=url, body=params)
        if response['status'] != 200:
            log.warning(response['reason'])
            return False
        (status, wechat_uuid) = self.reponse_process(response['data'])
        if status != '200' or not wechat_uuid:
            log.error("Error: status: %s, uuid: %s", status, wechat_uuid)
            return False
        self.uuid = wechat_uuid
        return True

    def reponse_process(self, data):
        re_match ='window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)"'
        match = re.search(re_match, data)
        if match:
            status = match.group(1)
            wechat_uuid = match.group(2)
            return(status, wechat_uuid)
        else:
            return None

    def show_qr_code(self):
        if self.status != 'Loging':
            log.error("Error: status is %s, Expect Loging", self.status)
            return False
        url = 'https://login.weixin.qq.com/l/' + self.uuid
        qr_store = qrcode.QRCode()
        qr_store.border = 1
        qr_store.add_data(url)
        qr_store.make()
        qr_store.print_ascii(invert=True)
        return True

    def wait_login(self, tip=1):
        if self.status != 'WaitLoging':
            log.error("Error: Status is %s, expect 'WaitLoging'", self.status)
            return False
        url = self.login_url + \
              '/cgi-bin/mmwebwx-bin/login?tip=%s&uuid=%s&_=%s' % \
              (tip, self.uuid, int(time.time()))
        response = get_url_data(url)
        if response['status'] != 200:
            log.error("Error: %s", response['reason'])
            return False
        match = re.search(r"window.code=(\d+);", response['data'])
        state = match.group(1)
        if state == '201':
            return True
        elif state == '200':
            match = re.search(r'window.redirect_uri="(\S+?)";', response['data'])
            r_uri = match.group(1) + '&fun=new'
            self.redirect_uri = r_uri
            self.base_url = r_uri[:r_uri.rfind('/')]
            return True
        elif state == '408':
            log.error("Error: Login timeout...")
            self.status = 'Timeout'
            return False
        else:
            log.error("Error: Login unknown error")
            self.status = 'UnknowError'
            return False

    
    def wechat_init(self):
        if self.status != 'Loged':
            log.error("Error: Status is %s, expect 'Loged'", self.status)
            return False

        response = get_url_data(self.redirect_uri)
        if response['status'] != 200:
            log.error("Error: Url response error: %s", response['reason'])
            return False
        doc = minidom.parseString(response['data'])
        root = doc.documentElement
        get_key = ['skey', 'wxsid',
                   'wxuin', 'pass_ticket']
        data = {}
        for node in root.childNodes:
            if node.nodeName in get_key:
                data[node.nodeName] = node.childNodes[0].data
        if '' in [ value for key, value in data.items()]:
            log.error("Error: Init response has null value...")
            return False
        self.pass_ticket = data['pass_ticket']
        self.skey = data['skey']
        self.request_parm = {
                'Uin': data['wxuin'],
                'Sid': data['wxsid'],
                'Skey': data['skey'],
                'DeviceID': 'e'+repr(random.random())[2:17],
                }
        url = self.base_url + '/webwxinit?pass_ticket=%s&skey=%s&r=%s' % (
                self.pass_ticket, self.skey, int(time.time()))
        headers = {
                'ContentType': 'application/json; charset=UTF-8',
                }
        params = {
                'BaseRequest': self.request_parm,
                }
        response = get_url_data(url=url, headers=headers, body=params, jsonfmt=True)
        if response['status'] != 200:
            log.error("Error: %s", response['reason'])
            return False
        self.synckey_dict = response['data']['SyncKey']
        self.user = response['data']['User']
        print(self.synckey_dict)
        print(self.user)
        #self.synckey = '|'.join(
        #        [str(key_val['key']) + '_' + str(key_val['val']) for key_val in self.synckey_dict['List']])
        return response['data']['BaseResponse']['Ret'] == 0


    def run(self):
        if not self.login():
            log.error("Error: Loging error...")
            return False
        if not self.wechat_init():
            log.error("Error: Init error...")
            return False
        


if __name__ == '__main__':
    w = WebWeChat()
    print(w.run())

