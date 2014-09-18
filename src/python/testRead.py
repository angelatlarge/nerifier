#!/usr/bin/env python

import os, sys
from nrf24L01p import Nrf, Reg, Cmd
import select
import argparse
import nrf_args
import kiot

graphite_paths = { 0xA0: "breadboard.lightsensor.1", 0xA1: "breadboard.tempsensor.1"}

class Reader:
  def __init__(self, args):
    self.nrf = None
    self.args = args
    pass

  def run(self):

    # reopen stdout file descriptor with write mode
    # and 0 as the buffer size (unbuffered)
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

    self.nrf = Nrf(
      recAddrPlsize=nrf_args.constructRecAddrPlsize(self.args),
      channel=self.args.channel,
      crcBytes=self.args.crc)
    self.printRegisterMap()

    self.sender = kiot.KiotSender(self.args.carbon_server, self.args.carbon_port, graphite_paths)

    self.read_list = [sys.stdin]
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
      packet = kiot.parseKiotPayload(payload)
      self.sender.send(packet.dataIndex, packet.dataValue)
      # print "Got packed from channel %d:", ",".join((("0x%02X" % (byte)) for byte in payload))


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--carbon_port', type=int, default=2003)
  parser.add_argument('--carbon_server', type=str, default="127.0.0.1")
  nrf_args.addNrfArgs(parser)
  r = Reader(parser.parse_args())
  r.run()


if __name__ == '__main__':
  main()