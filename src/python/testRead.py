#!/usr/bin/env python

import os, sys
from nrf24L01p import Nrf, Reg, Cmd, NrfPipe
import select
import argparse
import nrf_args
from struct import *
import traceback
import socket
import time


CARBON_SERVER = 'ec2-54-165-149-202.compute-1.amazonaws.com'
CARBON_PORT = 2003
graphite_paths = { 0xA0: "breadboard.lightsensor.1"}

class Reader:
  def __init__(self, args):
    self.nrf = None
    self.args = args
    pass

  def run(self):

    # reopen stdout file descriptor with write mode
    # and 0 as the buffer size (unbuffered)
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

    # nrf = Nrf(recAddrPlsize=([0xDE, 0xAD, 0xBE, 0xEF, 0xAE], 4), channel=0x7A)
    # nrf = Nrf(recAddrPlsize=([0xAE, 0xEF, 0xBE, 0xAD, 0xDE], 4), channel=channelNum)
    # nrf = Nrf(recAddrPlsize=([0xAE, 0xEF, 0xBE, 0x34, 0x12], 4), channel=channelNum)
    # nrf = Nrf(recAddrPlsize=([0x12, 0x34, 0x56, 0x78, 0x9A], 4))
    # self.nrf = Nrf(recAddrPlsize=([0x9A, 0x78, 0x56, 0x34, 0x12], self.args))
    self.nrf = Nrf(recAddrPlsize=nrf_args.constructRecAddrPlsize(self.args), channel=self.args.channel)
    # self.nrf = Nrf(recAddrPlsize=[NrfPipe([0x12, 0x34, 0x56, 0x78, 0x9A], 4)], channel=self.args.channel)
    # self.nrf = Nrf(recAddrPlsize=[NrfPipe([0x12, 0x34, 0x56, 0x78, 0x9A], 6)], channel=self.args.channel)
    self.printRegisterMap()

    # files monitored for input
    self.read_list = [sys.stdin]
    # select() should wait for this many seconds for input.
    # A smaller number means more cpu usage, but a greater one
    # means a more noticeable delay between input becoming
    # available and the program starting to work on it.
    self.readTimeout = 0.1 # seconds

    # while still waiting for input on at least one file
    print "Waiting for input..."
    while self.read_list:
      if not self.checkProcessInput():
        self.readPrintOutput()

  def checkProcessInput(self):
    ready = select.select(self.read_list, [], [], self.readTimeout)[0]
    if ready:
      for file in ready:
        line = file.readline()
        if not line: # EOF, remove file from input list
          print "Exiting..."
          self.read_list.remove(file)
        else:
          input = line.rstrip().lower()
          words = input.split()
          try:
            if words[0] == "c" or words[0] == "ch":
              # Set channel
              try:
                channelNum = int(words[1])
              except IndexError:
                pass
              print "Setting channel to %d..." % (channelNum)
              self.nrf.writeRegister(Reg.RF_CH, channelNum)
            elif input == "x":
              # Clear status
              print "Clearing STATUS..."
              self.nrf.writeRegister(Reg.STATUS, 0x7F)
            elif input == "z":
              # Clear RX buffer
              print "Clearing BUFFER..."
              self.nrf.command(Cmd.FLUSH_RX)
            elif input == "r":
              # Registers
              self.printRegisterMap()
            else:
              print "Unknown command"
          except IndexError:
            self.printRegisterMap()
          print "Waiting for input..."
    return ready

  def printRegisterMap(self):
    for regIdx in range(0, Reg.FEATURE+1):
      registerSize = 5 if regIdx in range(Reg.RX_ADDR_P0, Reg.RX_ADDR_P5 + 1) else 1
      registerData = list(self.nrf.readRegister(regIdx, registerSize))
      outputString = "Register %03x: [%s]" % (regIdx, ",".join(("%02x" % (ord(byte)) for byte in registerData)))
      if registerSize==1:
        outputString += " " + '{:08b}'.format(ord(registerData[0]))
      print outputString

  def readPrintOutput(self):
    """
    Reads NRF transmission and prints the data
    """
    data = self.nrf.read()
    if data:
      sourceIndex, payload = data
      print ("Got data on pipe %d" % (sourceIndex)), [ord(byte) for byte in payload]
      parseSendKiotPayload(payload)
      # print "Got packed from channel %d:", ",".join((("0x%02X" % (byte)) for byte in payload))


def parseSendKiotPayload(data):
  try:
    (dataIndex, dataType) = unpack('BB', data[0:2])
    if dataType == 3:
      dataValue = unpack('!l', data[4:8])[0]
      dataDescription = "32-bit uint"
    else:
      raise Exception("Unknown data type %d" % (dataType))
    print "KiotPacket: index %d %s " % (dataIndex, dataDescription), dataValue
    sendToGraphite(dataIndex, dataValue)
  except Exception as e: print "Failed to parse packet", e, traceback.print_exc()

def sendToGraphite(dataIndex, dataValue):
  global graphite_paths, CARBON_SERVER, CARBON_PORT
  try:
    graphitePath = graphite_paths[dataIndex]
    message = '%s %s %d' % (graphitePath, str(dataValue), int(time.time()))
    print 'sending message: %s' % message,
    sock = socket.socket()
    try:
      sock.connect((CARBON_SERVER, CARBON_PORT))
      sock.sendall(message + "\n")
      print "...sent",
    finally:
      print ""
      sock.close()
  except Exception as e: print "Failed to send data to graphite", e, traceback.print_exc()




def main():
  parser = argparse.ArgumentParser()
  nrf_args.addNrfArgs(parser)
  r = Reader(parser.parse_args())
  r.run()


if __name__ == '__main__':
  main()