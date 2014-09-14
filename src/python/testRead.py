#!/usr/bin/env python

import os, sys
from nrf24L01p import Nrf, Reg, Cmd, NrfPipe
import select
import argparse



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
    self.nrf = Nrf(recAddrPlsize=self.constructRecAddrPlsize(self.args), channel=self.args.channel)
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

  @staticmethod
  def constructRecAddrPlsize(args):
    nrfPipes = []
    for idxPipe in range(6):
      pipeAddressAttribute =  args.__dict__["pipe%daddress" % (idxPipe)]
      pipeSizeAttribute = args.__dict__["pipe%dsize" % (idxPipe)]
      newPipe = None
      # pipeSizeAttribute: -1 means dunamic, zero means pipe disabled
      if pipeSizeAttribute != 0:
        pipeAddress = [int("0x"+pipeAddressAttribute[i:i+2], 0) for i in range(0, len(pipeAddressAttribute), 2)]
        print "Args: have pipe %d address:" % (idxPipe), pipeAddress
        print "Args: have pipe %d argument:" % (idxPipe), pipeSizeAttribute
        payloadSize = None if pipeSizeAttribute == -1 else pipeSizeAttribute
        print "Args: setting pipe %d payload size to " % (idxPipe), payloadSize
        newPipe = NrfPipe(address=pipeAddress, payloadSize=payloadSize)
      else:
        print "Args: have no pipe %d" % (idxPipe)
      nrfPipes.append(newPipe)

    print nrfPipes
    return nrfPipes

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
      outputString = "Register %03x: [%s]" % (regIdx, ",".join(("%02x" % (byte) for byte in registerData)))
      if registerSize==1:
        outputString += " " + '{:08b}'.format(registerData[0])
      print outputString

  def readPrintOutput(self):
    """
    Reads NRF transmission and prints the data
    """
    data = self.nrf.read()
    if data:
      sourceIndex, payload = data
      print ("Got data on pipe %d" % (sourceIndex)), list(payload)
      # print "Got packed from channel %d:", ",".join((("0x%02X" % (byte)) for byte in payload))



def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('-c', '--channel', default=0x04)
  parser.add_argument('-p0a', '--pipe0address', type=str, default="9a78563412")
  parser.add_argument('-p0s', '--pipe0size',    type=int, default=4)
  parser.add_argument('-p1a', '--pipe1address', type=str, default=None)
  parser.add_argument('-p1s', '--pipe1size',    type=int, default=0)
  parser.add_argument('-p2a', '--pipe2address', type=str, default=None)
  parser.add_argument('-p2s', '--pipe2size',    type=int, default=0)
  parser.add_argument('-p3a', '--pipe3address', type=str, default=None)
  parser.add_argument('-p3s', '--pipe3size',    type=int, default=0)
  parser.add_argument('-p4a', '--pipe4address', type=str, default=None)
  parser.add_argument('-p4s', '--pipe4size',    type=int, default=0)
  parser.add_argument('-p5a', '--pipe5address', type=str, default=None)
  parser.add_argument('-p5s', '--pipe5size',    type=int, default=0)
  r = Reader(parser.parse_args())
  r.run()


if __name__ == '__main__':
  main()