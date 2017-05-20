#!/usr/bin/python3

from wechat_api import wechat
import logging
import time
log = logging.getLogger()
log.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
fm = logging.Formatter("%(asctime)s [%(filename)s:%(lineno)d] %(levelname)s: %(message)s")
ch.setFormatter(fm)
log.addHandler(ch)
def main():
    log.info("Start webwechat")
    wx = wechat.WebWeChat()
    wx.run()
    #wx.send_message('爱你哟', '小丢丢')
    #wx.send_message('i love you', '小丢丢')



if __name__ == '__main__':
    main()
