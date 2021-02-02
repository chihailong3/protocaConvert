#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
@Time :2021/1/25   : 16:44
@Author: Chi.hl
@Company: BITC.cn
@Description: protocaConvert

Copyright © 2019, BITC, Co,. Ltd. All Rights Reserved.
"""

# ! /usr/bin/env python
# coding=utf-8
# //   作用： 将主站的串口报文转换成从站的网络接口的报文格式 从站以广播的形式接受串口
# //            过来的数据 ；
# //      port： 本地串口名称
# //      slave_host_list ： 从站的IP地址和端口

from socket import *

import os
import select ,logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s : %(message)s')
logger = logging.getLogger(__name__)
import serial
import serial.tools.list_ports

import  json ,sys
# host_list = {
#     "192.168.56.1": 8899,
#     "192.169.11.106": 8877
# }
host_list = {}
ip_list = []
input  = []
need_connect_list = []
serial_name = ''
is_running =True
def read_config( ):
    # 读取json文件内容,返回字典格式
    logger.info (os.getcwd())
    try:
        with open('.//config.json','r',encoding='utf8')as fp:
            json_data = json.load(fp)
            global host_list,need_connect_list,ip_list,serial_name
            serial_name = json_data['port']
            slave_list = json_data['slave_host_list']
            for slave in slave_list:
                host_list[slave['ip']] = slave['port']
            ip_list = [i for i in host_list.keys()]
            need_connect_list = ip_list
            print('Config json data :' )
            print('____________________________')
            print('{}'.format(json_data) )

            print('____________________________')
    except Exception as e:
        global is_running
        logger.error("{}".format(e))
        is_running =False
        sys.exit(-1)
def mkpty():
    # 打开伪终端
    global serial_name
    plist = list(serial.tools.list_ports.comports())

    if len(plist) <= 0:
        print("The Serial port can't find!")
    else:
        plist_0 = list(plist[0])
        for sname in plist_0:
            if str(sname).upper() ==  serial_name.upper():
                serial_name = serial_name.upper()
                break
        else:
            logger.error('Port:{} does not exists in this machine!')
            global is_running

            is_running = False
            sys.exit(-1)

        serialFd = serial.Serial(serial_name, 9600, timeout=60)
        return serialFd

import threading,time

class CThreadUartReceive(threading.Thread):
    def __init__(self, ser,sockets):
        threading.Thread.__init__(self)
        self.ser = ser
        self.sockets =sockets


    def run(self):
        global is_running
        while is_running:
            if self.ser.isOpen() == False:
                time.sleep(0.1)
                continue
            while is_running:
                time.sleep(0.1)
                n = self.ser.inWaiting()
                if n == 0:
                    break
                else:
                    data = self.ser.read(n)
                    try:
                        for client in self.sockets:
                            client.send(data)
                    except error:
                        pass



def udp_broadcast_test():


    # ipv4        SOCK_DGRAM指定了这个Socket的类型是UDP
    s = socket(AF_INET, SOCK_DGRAM)
    s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    # 绑定 客户端口和地址:
    s.bind(('', 6003))
    print ('Bind UDP on 6003...')
    while True:
        # 接收数据 自动阻塞 等待客户端请求:
        data, addr = s.recvfrom(1024)
        message = 'Received from %s:%s.' % (addr, data)
        print(message)



class SingletonType(type):
    _instance_lock = threading.Lock()
    def __call__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            with SingletonType._instance_lock:
                if not hasattr(cls, "_instance"):
                    cls._instance = super(SingletonType,cls).__call__(*args, **kwargs)
        return cls._instance

class Foo(metaclass=SingletonType):
    def __init__(self,name):
        self.name = name


# obj1 = Foo('name')
# obj2 = Foo('name')
# print(obj1,obj2)

def singleton(cls):
    # 单下划线的作用是这个变量只能在当前模块里访问,仅仅是一种提示作用
    # 创建一个字典用来保存类的实例对象
    _instance = {}

    def _singleton(*args, **kwargs):
        # 先判断这个类有没有对象
        if cls not in _instance:
            _instance[cls] = cls(*args, **kwargs)  # 创建一个对象,并保存到字典当中
        # 将实例对象返回
        return _instance[cls]

    return _singleton


@singleton
class CThreadSetUpConnection(threading.Thread):

    def __init__(self  ):
        threading.Thread.__init__(self)
        #self.need_connect_list = need_connect_list
        self.isconnecting = True
    def isConnecting(self):
        return  self.isconnecting
        pass
    def doconnect(self):
        global  need_connect_list
        for ip in need_connect_list:
            tcp_client_socket = socket(AF_INET, SOCK_STREAM)
            tcp_client_socket.settimeout(100)
            try:
                print("Connect to {} ...!!".format(ip))
                self.isconnecting = True
                tcp_client_socket.connect((ip, host_list[ip]))
                print("{} connected!!".format(ip))
            except error:
                pass
            else:
                input.append(tcp_client_socket)
                need_connect_list =list( set(need_connect_list) -{ip})

        pass

    def run(self):
        global need_connect_list ,is_running
        while is_running:
            while need_connect_list:
                self.doconnect()
                time.sleep(0.2)
            self.isconnecting =False
            #print("Connecting is finished!!")
            time.sleep(1)






def test_modbus_to_tcp():
    # 创建socket
    socketlist = []
    global  input,need_connect_list
    # 配置tcp服务端ip和端口
    recvData=[]
    con = CThreadSetUpConnection()
    con.start()
    # Waiting until at least one device is connected
    while not len(input):
        time.sleep(0.5)
    master1 = mkpty()
    serPort = CThreadUartReceive(master1,input)
    serPort.start()
     
    while True:
        while len(input)>0:

            rl, wl, el = select.select(input, [], [], 1)
            for e in el:
                print ("el = ",el )
            for master in rl:
                if master == master1:
                    data = os.read(master, 128)
                    print ("read %d data." % len(data))
                    for client in input:
                        client.send(data)
                    print( "TCP SEND %d data." % len(data))

                if master in input:
                    try:
                         recvData = master.recv(1024)
                    except error:
                        pass

                    if   len(recvData)>0:
                        print('接收到的数据为:', recvData)
                        master1.write( recvData)
                    else: #断开连接
                        print('closing', master)
                        # Stop listening for input on the connection

                        input.remove(master)
                        peerinfo = master.getpeername()
                        master.close()
                        time.sleep(2)
                        isDisConnecting = True
                        stmp = set(need_connect_list)
                        stmp.add(peerinfo[0])
                        need_connect_list = list(stmp)
    #                    need_connect_list.append(peerinfo[0])
    #                     conn = CThreadSetUpConnection()
    #                     if not conn.isConnecting():
    #                         conn.start()
                        time.sleep(0.2)

        # 关闭套接字
        print("all socket is closed!!")
        time.sleep(1)


if __name__ == '__main__':
    read_config()
    test_modbus_to_tcp()

