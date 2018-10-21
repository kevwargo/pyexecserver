#!/usr/bin/python3

from threading import Thread
from socket import socket, SOL_SOCKET, SO_REUSEADDR
from struct import pack, unpack
import os, sys
import argparse
import subprocess
from os.path import dirname, realpath, join as pjoin

Port = None
Globals = None
PyExecThread = None

class PyExecServer:

    def __init__(self, port, _globals):
        self.port = port
        self.globals = _globals
        self.thread = Thread(name='pyexec-thread', target=self.run, daemon=True)

    def run(self):
        s = socket()
        s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        s.bind(('localhost', self.port))
        s.listen(5)
        with s:
            while True:
                c, a = s.accept()
                with c:
                    size = unpack('I', c.recv(4))[0]
                    buf = b''
                    while len(buf) < size:
                        buf += c.recv(size - len(buf))
                expr = buf.decode()
                try:
                    exec(expr, self.globals)
                except:
                    print('Expression ' + repr(expr))
                    raise

    def start(self):
        self.thread.start()

    def restart(self):
        self.thread = Thread(name='pyexec-thread', target=self.run, daemon=True)
        self.start()


def send(port, filename):
    s = socket()
    s.connect(('localhost', port))
    if filename != '-':
        with open(filename, 'rb') as f:
            data = f.read()
    else:
        data = sys.stdin.read().encode()
    print(data)
    s.send(pack('I', len(data)) + data)

def main():
    parser = argparse.ArgumentParser(description='If neither --exec-stdin or --exec-file are specified run interactive interpreter with "pyexecserver" variable bound to listening exec server')
    parser.add_argument('-p', '--port', type=int, default=35000, help='port to connect to or listen on')
    parser.add_argument('-a', '--address', default='localhost', help='host to connect to')
    parser.add_argument('-i', '--exec-stdin', default=False, action='store_true')
    parser.add_argument('-f', '--exec-file')
    parser.add_argument('--python', default='python', help='specify custom python executable to run interactive interpreter')
    ns = parser.parse_args()
    if ns.exec_file or ns.exec_stdin:
        if ns.exec_file:
            with open(ns.exec_file, 'rb') as f:
                data = f.read()
        else:
            data = sys.stdin.read().encode()
        with socket() as s:
            s.connect((ns.address, ns.port))
            s.send(pack('I', len(data)) + data)
    else:
        env = os.environ.copy()
        if 'PYTHONSTARTUP' in env:
            env['ORIGINAL_PYTHONSTARTUP'] = env['PYTHONSTARTUP']
        env['PYTHONSTARTUP'] = pjoin(dirname(realpath(__file__)), 'pythonstartup')
        exit(subprocess.run([ns.python], env=env).returncode)

if __name__ == '__main__':
    main()
