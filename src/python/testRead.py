#!/usr/bin/env python

import os, sys
from nrf24L01p import Nrf, Reg
import select

nrf = None


# files monitored for input
read_list = [sys.stdin]
# select() should wait for this many seconds for input.
# A smaller number means more cpu usage, but a greater one
# means a more noticeable delay between input becoming
# available and the program starting to work on it.
timeout = 0.1 # seconds

channelNum=0x30

def main():
  global nrf
  global read_list
  global channelNum
  # reopen stdout file descriptor with write mode
  # and 0 as the buffer size (unbuffered)
  sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

  # nrf = Nrf(recAddrPlsize=([0xDE, 0xAD, 0xBE, 0xEF, 0xAE], 4), channel=0x7A)
  # nrf = Nrf(recAddrPlsize=([0xAE, 0xEF, 0xBE, 0xAD, 0xDE], 4), channel=channelNum)
  # nrf = Nrf(recAddrPlsize=([0xAE, 0xEF, 0xBE, 0x34, 0x12], 4), channel=channelNum)
  # nrf = Nrf(recAddrPlsize=([0x12, 0x34, 0x56, 0x78, 0x9A], 4))
  nrf = Nrf(recAddrPlsize=([0x9A, 0x78, 0x56, 0x34, 0x12], 4))
  printRegisterMap()

  # while still waiting for input on at least one file
  print "Waiting for input..."
  while read_list:

    ready = select.select(read_list, [], [], timeout)[0]
    if not ready:
      readPrintOutput()
    else:
      for file in ready:
        line = file.readline()
        if not line: # EOF, remove file from input list
          print "Exiting..."
          read_list.remove(file)
        else:
          input = line.rstrip().lower()
          words = input.split()
          try:
            if words[0] == "c":
              try:
                channelNum = int(words[1])
              except IndexError:
                pass
              print "Setting channel to %d..." % (channelNum)
              nrf.writeRegister(Reg.RF_CH, channelNum)
            elif input == "x":
              print "Clearing STATUS..."
              nrf.writeRegister(Reg.STATUS, 0x7F)
            else:
              printRegisterMap()
          except IndexError:
            printRegisterMap()

          print "Waiting for input..."

def readPrintOutput():
  global nrf
  data = nrf.read()
  if data:
    sourceIndex, payload = data
    print ("Got data on pipe %d" % (sourceIndex)), list(payload)
    # print "Got packed from channel %d:", ",".join((("0x%02X" % (byte)) for byte in payload))

def printRegisterMap():
  global nrf
  for regIdx in range(0, Reg.FEATURE+1):
    registerSize = 5 if regIdx in range(Reg.RX_ADDR_P0, Reg.RX_ADDR_P5 + 1) else 1
    registerData = list(nrf.readRegister(regIdx, registerSize))
    outputString = "Register %03x: [%s]" % (regIdx, ",".join(("%02x" % (byte) for byte in registerData)))
    if registerSize==1:
      outputString += " " + '{:08b}'.format(registerData[0])
    print outputString


if __name__ == '__main__':
  main()