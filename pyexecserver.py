#!/usr/bin/python3

import argparse
import os
import sys
from os.path import dirname
from os.path import join as pjoin
from os.path import realpath
from socket import SO_REUSEADDR, SOL_SOCKET, socket
from struct import pack, unpack
from threading import Thread
from traceback import print_exc, print_stack

Port = None
Globals = None
PyExecThread = None


class PyExecServer:
    def __init__(self, port, _globals):
        self.port = port
        self.globals = _globals
        self._create_thread()

    def _create_thread(self):
        self._thread = Thread(name="pyexec-thread", target=self.run, daemon=True)

    def run(self):
        s = socket()
        s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        s.bind(("localhost", self.port))
        s.listen(5)
        with s:
            while True:
                c, a = s.accept()
                with c:
                    size = unpack("I", c.recv(4))[0]
                    buf = b""
                    while len(buf) < size:
                        buf += c.recv(size - len(buf))
                expr = buf.decode()
                try:
                    exec(expr, self.globals)
                except:
                    print("Expression " + repr(expr))
                    print_exc()
                    print_stack()

    def start(self):
        self._thread.start()

    def restart(self):
        self._create_thread()
        self.start()


def main():
    parser = argparse.ArgumentParser(
        description='If neither --exec-stdin or --exec-file are specified run interactive interpreter with "pyexecserver" variable bound to listening exec server'
    )
    parser.add_argument(
        "-p", "--port", type=int, default=35000, help="port to connect to or listen on"
    )
    parser.add_argument(
        "-a", "--address", default="localhost", help="host to connect to"
    )
    parser.add_argument("-i", "--exec-stdin", default=False, action="store_true")
    parser.add_argument("-f", "--exec-file")
    parser.add_argument(
        "--python",
        default="python",
        help="specify custom python executable to run interactive interpreter",
    )
    ns = parser.parse_args()
    if ns.exec_file or ns.exec_stdin:
        if ns.exec_file:
            with open(ns.exec_file, "rb") as f:
                data = f.read()
        else:
            data = sys.stdin.read().encode()
        with socket() as s:
            s.connect((ns.address, ns.port))
            s.send(pack("I", len(data)) + data)
    else:
        env = os.environ.copy()
        if "PYTHONSTARTUP" in env:
            env["ORIGINAL_PYTHONSTARTUP"] = env["PYTHONSTARTUP"]
        env["PYTHONSTARTUP"] = pjoin(dirname(realpath(__file__)), "pythonstartup")
        env["PYEXECPORT"] = str(ns.port)
        env["PYEXECADDR"] = ns.address
        os.execvpe(ns.python, [ns.python], env)


if __name__ == "__main__":
    main()
