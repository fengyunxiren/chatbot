#!/usr/bin/python3

import uuid
import logging
import os
import time
import datetime
import re
import qrcode
from xml.dom import minidom
from chatbot.url_method.url_requests import url_requests
from chatbot.chat_api.tuling import chat
import random

log = logging.getLogger(__name__)

import requests

SYNC_HOSTS = [
        'https://wx2.qq.com',
        'https://webpush.wx2.qq.com',
        'https://wx8.qq.com',
        'https://webpush.wx8.qq.com',
        'https://webpush.wx.qq.com',
        'https://webpush.web2.wechat.com',
        'https://wechat.com',
        'https://webpush.web.wechat.com',
        'https://webpush.weixin.qq.com',
        'https://webpush.wechat.com',
        'https://webpush1.wechat.com',
        'https://webpush2.wechat.com',
        'https://webpush.wx.qq.com',
        'https://webpush2.wx.qq.com',
        ]


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
        self.contact_list = []
        self.sync_host = ''
        self.device_id = 'e' + repr(random.random())[2:17]
        self.cookies = dict()

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
        log.info("Log wechat succeed!")
        return self.status == 'Loged'


    def get_uuid(self):
        url = 'https://login.weixin.qq.com/jslogin'
        params = {
                'appid': self.appid,
                'fun': 'new',
                'lang': self.lang,
                '_': int(time.time()),
                }
        resp = url_requests('post', url=url, data=params)
        if not resp:
            self.status = "LogError"
            return False
        (status, wechat_uuid) = self.reponse_process(resp)
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
        resp = url_requests('get', url=url)
        if not resp:
            self.status = 'LogError'
            return False
        match = re.search(r"window.code=(\d+);", resp)
        state = match.group(1)
        if state == '201':
            return True
        elif state == '200':
            match = re.search(r'window.redirect_uri="(\S+?)";', resp)
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
        log.info("Start init wechat.")
        self.status = 'Init'
        resp = url_requests('get', self.redirect_uri,
                             cookies=self.cookies)
        if not resp:
            self.status = 'InitError'
            return False
        else:
            resp, cookies = resp
            if cookies and cookies != self.cookies:
                self.cookies = cookies
        doc = minidom.parseString(resp)
        root = doc.documentElement
        get_key = ['skey', 'wxsid',
                   'wxuin', 'pass_ticket']
        data = {}
        for node in root.childNodes:
            if node.nodeName in get_key:
                data[node.nodeName] = node.childNodes[0].data
        if '' in [ value for key, value in data.items()]:
            log.error("Error: Init response has null value...")
            self.status = 'InitError'
            return False
        self.pass_ticket = data['pass_ticket']
        self.skey = data['skey']
        self.sid = data['wxsid']
        self.uin = data['wxuin']
        self.request_parm = {
                'Uin': int(data['wxuin']),
                'Sid': data['wxsid'],
                'Skey': data['skey'],
                'DeviceID': self.device_id,
                }
        url = self.base_url + '/webwxinit'
        headers = {
                'ContentType': 'application/json; charset=UTF-8',
                }
        params = {
                'pass_ticket': self.pass_ticket,
                'skey': self.skey,
                'r': int(time.time())
                }
        data = {
                  'BaseRequest': self.request_parm,
                 }
        resp, cookies = url_requests('post', url=url, headers=headers, 
                                      params=params, cookies = self.cookies,
                                      data=data, jsonfmt=True)
        if not resp:
            log.error("Error: %s", "Get user information error!")
            return False
        if cookies and cookies != self.cookies:
            self.cookies = cookies
        self.synckey_dict = resp['SyncKey']
        self.user = resp['User']
        self.synckey = '|'.join(
                [str(key_val['Key']) + '_' + str(key_val['Val']) \
                    for key_val in self.synckey_dict['List']])
        self.status = "Inited"
        log.info("Init wechat succeed!")
        return resp['BaseResponse']['Ret'] == 0


    def wechat_notify(self):
        if self.status != 'Inited':
            log.error('Init error, can not set notify')
            return False
        self.state = "SetNotify"
        url = self.base_url + '/webwxstatusnotify'
        params = {
                'lang': self.lang,
                'pass_ticket': self.pass_ticket,
                }
        data = {
                'BaseRequest': self.request_parm,
                'Code': 3,
                'FromUserName': self.user['UserName'],
                'ToUserName': self.user['UserName'],
                'ClientMsgId': int(time.time())
                }
        resp = url_requests('post', url=url, params=params,
                            data=data, jsonfmt=True)
        if not resp:
            log.error("Error: Set notify error!")
            self.status = 'SetError'
            return False
        if not  resp['BaseResponse']['Ret'] == 0:
            log.error("Error: %s", resp['BaseResponse']['ErrMsg'])
            self.status = 'SetError'
            return False
        self.status = 'SetSucceed'
        log.info('Set notify succeed.')
        return True

    def get_contact(self):
        url = self.base_url + '/webwxgetcontact'
        headers = {
                'ContentType': 'application/json, charset=UTF-8',
                }
        params = {
                'pass_ticket': self.pass_ticket,
                'skey': self.skey,
                'r': int(time.time()),
                }
        data = {
                'BaseRequest': self.request_parm,
                }
        resp = url_requests('post', url=url, headers=headers, 
                            params=params, data=data, jsonfmt=True)
        if not resp:
            log.error("Error: Get contact error!")
        self.contact_list = list()
        for contact in resp['MemberList']:
            if contact['VerifyFlag'] & 8 != 0:
                continue
            elif '@@' in contact['UserName']:
                continue
            elif contact['UserName'] == self.user['UserName']:
                continue
            self.contact_list.append(contact)
        return True

    def send_message(self, message, user):
        url = self.base_url + '/webwxsendmsg'
        params = {
                'pass_ticket': self.pass_ticket,
                }
        msg_id = str(int(time.time() * 10000)) + \
                 str(random.random())[:5].replace('.', '')

        params = {
                'pass_ticket': self.pass_ticket,
                }
        user_id = self.get_user_id(user)
        if not user_id:
            log.error("Not found user in contact...")
            return False
        data = {
                'BaseRequest': self.request_parm,
                'Msg': {
                    'Type': 1,
                    'Content': self.translate_message(message),
                    'FromUserName': self.user['UserName'],
                    'ToUserName': user_id,
                    'LocalID': msg_id,
                    'ClientMsgId': msg_id,
                    }
                }
        headers = {
                'content-type': 'application/json; charset=UTF-8',
                }
        resp = url_requests('post', url=url, headers=headers,
                            params=params, data=data, jsonfmt=True)
        if not resp:
            log.error("Error: Send message error")
            return False

        if resp['BaseResponse']['Ret'] != 0:
            log.error("Error: Send message error, %s", resp)
            return False
        log.info("Send message succeed.")
        return True


    def get_user_id(self, user):
        if not self.contact_list:
            self.get_contact()
        for contact in self.contact_list:
            if contact['NickName'] == user or contact['RemarkName'] == user\
                    or contact['UserName'] == user:
                return contact['UserName']
        log.warning("No Friend named %s", user)
        return None

    def get_user_name(self, identity):
        if identity == self.user['UserName']:
            if self.user['RemarkName']:
                return self.user['RemarkName']
            else:
                return self.user['NickName']
        if not self.contact_list:
            self.get_contact()
        for contact in self.contact_list:
            if contact['UserName'] == identity:
                if contact['RemarkName']:
                    return contact['RemarkName']
                else:
                    return contact['NickName']
        return identity


    def translate_message(self, message):
        if not message:
            return message
        if isinstance(message, str):
            return message

    def get_sync_host(self):
        for host in SYNC_HOSTS:
            sync_check = self.do_sync(host)
            if sync_check:
                if sync_check[0] == '0':
                    self.sync_host = host
                    log.info("Get sync host succeed!")
                    return True
        return False

    def do_sync(self, host=None):
        log.info("Do sync check...")
        if host is None:
            if not self.sync_host:
                state = self.get_sync_host()
                if not state:
                    log.error("Error: Can not get sync host!")
                    return (-1, -1)
            host = self.sync_host

        url = host + '/cgi-bin/mmwebwx-bin/synccheck'
        headers = {
                'Referer': 'https://wx.qq.com/',
                }
        params = {
                'r': int(time.time()),
                'sid': self.sid,
                'uin': self.uin,
                'skey': self.skey,
                'deviceid': self.device_id,
                'synckey': self.synckey,
                '_': int(time.time()),
                }
        data = {
                  'BaseRequest': self.request_parm,
                 }
        content = url_requests('get', url=url, 
                                     headers=headers, params=params,
                                     data=data, cookies=self.cookies)
        if not content:
            log.error("Error: Do sync error.")
            return (-1, -1)
        else:
            resp, cookies = content
        if cookies and cookies != self.cookies:
            self.cookies = cookies
        pm = re.search(
                r'window.synccheck={retcode:"(\d+)",selector:"(\d+)"}', resp)
        retcode = pm.group(1)
        selector = pm.group(2)
        log.info("Sync check done...")
        return (retcode, selector)


    def get_message(self):
        url = self.base_url + '/webwxsync'
        params = {
                'sid': self.sid,
                'skey': self.skey,
                'pass_ticket': self.pass_ticket,
                }
        data = {
                'BaseRequest': self.request_parm,
                'SyncKey': self.synckey_dict,
                'rr': ~int(time.time()),
                }
        resp = url_requests('post', url=url, params=params,
                            data=data, jsonfmt=True)
        if not resp:
            log.error("Error: Get message failed!")
            return None
        if resp['BaseResponse']['Ret'] == 0:
            self.synckey_dict = resp['SyncKey']
            self.synckey = '|'.join(
                    [str(key_val['Key']) + '_' + str(key_val['Val']) \
                        for key_val in self.synckey_dict['List']])
        return resp['AddMsgList']


    def listen_message(self):
        while True:
            retcode, selector = self.do_sync()
            if retcode == '0':
                if selector == '2':
                    messages = self.get_message()
                    self.handle_message(messages)
            time.sleep(self.interval)

    def handle_message(self, messages):
        log.info("You have new message, please check it.")
        for message in messages:
            if message['MsgType'] == 1:
                log.info("%s=>%s:",
                         self.get_user_name(message['FromUserName']),
                         self.get_user_name(message['ToUserName']))
                log.info("Message: %s", message['Content'])
                user_id = message['FromUserName'].strip('@')
                content = chat(message['Content'],userid=user_id)
                content = '[Robot]: ' + content
                log.info("%s=>%s:",
                         self.get_user_name(message['ToUserName']),
                         self.get_user_name(message['FromUserName']))
                log.info("Send: %s", content)
                self.send_message(content,
                                  message['FromUserName'])


    def run(self):
        if not self.login():
            log.error("Error: Loging error...")
            return False
        if not self.wechat_init():
            log.error("Error: Init error...")
            return False
        
        if not self.wechat_notify():
            log.error("Error: Set notify error...")
            return False

        if not self.get_contact():
            log.error("Error: Get contact error...")
            return False

        if not self.get_sync_host():
            log.error("Error: Get sync host error...")
            return False
        self.listen_message()
