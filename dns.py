import requests
import dnslib
import time
import sys
import socket
import os
import pickle
import threading

class DNS():

    def __init__(self):
        self.cache = {}
        self.request_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.request_socket.bind(('localhost', 53))
        self.request_socket.settimeout(0)
        self.receive_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.receive_socket.settimeout(0)

    def uploadCash(self):
        with open('cache.txt', 'rb') as f:
            try:
                self.cache = pickle.load(f)
                self.check_TTL()
            except Exception:
                pass

    def make_request(self):
        try:
            data, address = self.request_socket.recvfrom(1024)
        except OSError:
            data = None
        if data:
            ans = dnslib.DNSRecord.parse(data)
            question = ans.questions[0]
            if question.qname in self.cache:
                cache, ttl = self.cache[question.qname]
                print('Кешированная запись ' + str(question.qname) + ' время жизни записи ' + str(time.ctime(ttl)))
                print(cache)
                ans.questions.remove(question)
            else:
                print('Запись ' + str(question.qname))
            if ans.question:
                server = ("8.8.8.8", 53)
                self.receive_socket.sendto(ans.pack(), server)

    def take_receive(self):
        try:
            data, address = self.receive_socket.recvfrom(1024)
        except OSError:
            data = None
        if(data):
            ans = dnslib.DNSRecord.parse(data)
            print(ans)
            for question in ans.rr:
                self.cache[question.rname]= (ans, int(time.time()) + question.ttl)

    def check_TTL(self):
        for i in self.cache:
            cache, ttl = self.cache[i]
            if ttl < int(time.time()):
                del self.cache[i]

    def test_send(self, addr):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(dnslib.DNSRecord.question(addr).pack(), ("localhost", 53))
        s.close()


server_class = DNS()
print("В каком режиме мы хотите работать?")
print("test - тестовый, common - в режиме сервера")
t = input()
print("Сервер начал работу")
server_class.uploadCash()
try:
    if t == "test":
        while True:
            print("Введите адрес")
            inpu = input()
            server_class.test_send(str(inpu))
            server_class.make_request()
            time.sleep(0.2)
            server_class.take_receive()
            time.sleep(0.2)
            server_class.check_TTL()
    else:
        while True:
            server_class.make_request()
            server_class.take_receive()
            time.sleep(0.2)
            server_class.check_TTL()
except KeyboardInterrupt:
    print("Сервер успешно завершил работу")
except Exception as e:
    print("Сервер выключается из-за ошибки")
    print(e)
finally:
    server_class.request_socket.close()
    server_class.receive_socket.close()
    with open('cache.txt', 'wb') as f:
        pickle.dump(server_class.cache, f)
    time.sleep(1)
    sys.exit(0)
