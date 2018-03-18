#! /usr/bin/env python3

import socket
import argparse
import os
import time
import serial
import sys
import select

#---------------------------------------------------------------------------

class LoRaSerial:
    def __init__(self, args):
        self.args = args
        self.ser = serial.Serial(args.tty, 115200,
                                 timeout=args.poll_interval)
        self.pending = b""
        self.send_pending = []
        self.recv_pending = []
        self.state = "init"
        self.last_send_clock = time.time()
        self.last_info_clock = time.time()

    def show_info(self):
        if time.time() - self.last_info_clock > 1: # sec
            self.last_info_clock = time.time()
            print("State:", self.state, len(self.send_pending),
                  len(self.recv_pending))
        
    def get_line(self):
        while True:
            c = self.ser.read(1)
            if c == b"":
                return
            self.pending +=  c
            if c == b"\n":
                break
            if self.args.dbg_serial:
                sys.stdout.write(c.decode("utf-8"))
                sys.stdout.flush()
        pos = self.pending.find(b"\n")
        if pos >=0:
            result = self.pending[0:pos+1]
            self.pending = self.pending[pos+1:]
            return result
        else:
            return None

    def process(self):
        #print(self.state, len(self.send_pending))
        line = self.get_line()
        if line is None:
            line = b""
        if line.startswith(b"@@BOOT"):
            print("+> RIOT Init")
            self.state = "init"
        elif line.startswith(b"@@JOIN SUCCESS"):
            print("+> Join success")
            self.state = "running"
        elif line.startswith(b"@@JOIN FAILURE"):
            print("+> Join failure")
            self.state = "failure"
        elif line.startswith(b"@@READ"):
            self.state = "waiting"
            if len(self.send_pending) > 0:
                self._do_send(self.send_pending.pop(0))
                self.state = "running"
        elif line.startswith(b"@@WRITE"):
            self.state = "receiving"
            return self.process_line()
        elif line.startswith(b"@@SENT"):
            self.last_send_clock = time.time()            
            print("+> Sending done [%u]" % len(self.send_pending))
            self.state = "running"
        else:
            if self.state == "waiting" and len(self.send_pending) > 0:
                self._do_send(self.send_pending.pop(0))
                self.state = "running"            
            elif self.state == "receiving":
                print("DATA:", line)
                XXX
            else:
                if self.args.dbg_serial:                
                    print("DATA:", line)
                
    def _do_send(self, raw_data):
        hex_data = b"".join([b"%02x" % b for b in raw_data])
        print("+> lora-send " + hex_data.decode("utf-8"))
        #print("raw_data", raw_data, type(raw_data))        
        self.ser.write(hex_data+b"\n") # XXX: write timeout
        #print("send_as_hex %s" % hex_data)
        self.last_send_clock = time.time()

    def send(self, packet):
        self.last_send_clock = time.time()
        self.send_pending.append(packet)
        self.process()

#---------------------------------------------------------------------------

def test_lora_serial(args):
    lora_serial = LoRaSerial(args)
    time_start = time.time()
    while True:
        line = lora_serial.get_line()
        if line != None:
            print("\n","%.3f" % (time.time()-time_start), line, end="")
        else:
            sys.stdout.write(".")
        sys.stdout.flush()
            
#---------------------------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=9999,
                    help="destination port")
parser.add_argument("--tty", default="/dev/ttyACM0", help="mote /dev/tty...")
parser.add_argument("--poll-interval", default=0.01, type=float,
                    help="poll interval of the serial port/udp ports (seconds)")
parser.add_argument("--test-lora", default=False, action="store_true")
parser.add_argument("--dbg-serial", default=False, action="store_true")
parser.add_argument("--check-interval", default=10.0, type=float)
args = parser.parse_args()

#---------------------------------------------------------------------------

if args.test_lora:
    test_lora_serial(args)

#--------------------------------------------------

sd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sd.bind(("", args.port))
print("+ Listening UDP packets on port %s" % args.port)
lora_serial = LoRaSerial(args)
print("+ 'bridging' to LoRaWAN mote %s" % args.tty)

MAX_PACKET_SIZE = 100000
while True:
    sl1,sl2,sl3 = select.select([sd],[],[], args.poll_interval)
    lora_serial.show_info()
    if len(sl1) > 0:
        sp = len(lora_serial.send_pending)
        rp = len(lora_serial.recv_pending)
        packet, address = sd.recvfrom(MAX_PACKET_SIZE)
        print("+ received packet[{}|{}|{}]:".format(sp, rp, lora_serial.state),
              repr(packet), "from:", address)
        lora_serial.send(packet)
    else:
        lora_serial.process()
        #if (time.time() - lora_serial.last_send_clock > args.check_interval
        #    and len(lora_serial.send_pending) == 0):
        #    lora_serial.send(b"")

#---------------------------------------------------------------------------
