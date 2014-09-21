#!/usr/bin/env python

import os, sys
from nrf24L01p import Nrf, Reg, Cmd
import select
import argparse
import nrf_args
import kiot

graphite_paths = {
  0x00: "breadboard.lightsensor.1",
  0x01: "breadboard.tempsensor.1",
  0xA0: "breadboard.lightsensor.1",
  0xA1: "breadboard.tempsensor.1"
}

class Reader:
  def __init__(self, args):
    self.nrf = None
    self.args = args
    pass

  def run(self):

    # reopen stdout file descriptor with write mode
    # and 0 as the buffer size (unbuffered)
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

    if self.args.platform == "arietta":
      import spi_intf_arietta
      from spibus import Spibus
      from ablib import Pin
      import struct
      hardware_intf = spi_intf_arietta.SpiIntfArietta(
        spiBus=Spibus(device="/dev/spidev32766.0", readMode=struct.pack('I',0), writeMode=struct.pack('I',0)),
        cePin = Pin('J4.26','OUTPUT')
      )
    elif self.args.platform == "rpi":
      import spi_intf_rpi
      import spi
      import RPi.GPIO as GPIO
      hardware_intf = spi_intf_rpi.SpiIntfRPi(spi, GPIO, 25)

    self.nrf = Nrf(
      hardwareIntf = hardware_intf,
      recAddrPlsize=nrf_args.constructRecAddrPlsize(self.args),
      channel=self.args.channel,
      crcBytes=self.args.crc,
      speed=self.args.speed)
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
    for idx, name in {
      0x00:'CONFIG',
      0x01:'EN_AA',
      0x02:'EN_RXADDR',
      0x03:'SETUP_AW',
      0x04:'SETUP_RETR',
      0x05:'RF_CH',
      0x06:'RF_SETUP',
      0x07:'STATUS',
      0x08:'OBSERVE_TX',
      0x09:'RPD',
      0x0A:'RX_ADDR_P0',
      0x0B:'RX_ADDR_P1',
      0x0C:'RX_ADDR_P2',
      0x0D:'RX_ADDR_P3',
      0x0E:'RX_ADDR_P4',
      0x0F:'RX_ADDR_P6',
      0x10:'TX_ADDR',
      0x11:'RX_PW_P0',
      0x12:'RX_PW_P1',
      0x13:'RX_PW_P2',
      0x14:'RX_PW_P3',
      0x15:'RX_PW_P4',
      0x16:'RX_PW_P5',
      0x17:'FIFO_STATUS',
      0x1C:'DYNPD',
      0x1D:'FEATURE'
      }.iteritems():
      registerSize = 5 if idx in range(Reg.RX_ADDR_P0, Reg.TX_ADDR + 1) else 1
      registerData = list(self.nrf.readRegister(idx, registerSize))
      outputString = "Register %03x (%11s): [%s]" % (idx, name, ",".join(("%02x" % (ord(byte)) for byte in registerData)))
      if registerSize==1:
        outputString += " " + '{:08b}'.format(ord(registerData[0]))
      print outputString

  def readPrintOutput(self):
    """
    Reads NRF transmission and prints the data
    """
    data = self.nrf.read()
    for datum in data:
      sourceIndex, payload = datum
      print ("Got data on pipe %d" % (sourceIndex)), [ord(byte) for byte in payload]
      packet = kiot.parseKiotPayload(payload)
      self.sender.send(packet.dataIndex, packet.dataValue, packet.previousRetryCount)
      # print "Got packed from channel %d:", ",".join((("0x%02X" % (byte)) for byte in payload))


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('platform', choices=['arietta', 'rpi'])
  parser.add_argument('--carbon_port', type=int, default=2003)
  parser.add_argument('--carbon_server', type=str, default="127.0.0.1")
  nrf_args.addNrfArgs(parser)
  r = Reader(parser.parse_args())
  r.run()


if __name__ == '__main__':
  main()