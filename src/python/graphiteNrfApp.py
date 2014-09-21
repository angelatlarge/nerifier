#!/usr/bin/env python

import argparse
import yaml
import nrf24L01p
import kiot
import logging
import struct
import sys, time
import traceback

class Graphiter:
  def run(self):
    parser = argparse.ArgumentParser()
    parser.add_argument('platform', choices=['arietta', 'rpi'])
    parser.add_argument("-c", "--config", type=str, default="nrfconfig.yaml")
    parser.add_argument("-l", "--log", type=str)
    parser.add_argument("-L", "--loglevel", type=str, choices=['info', 'debug'], default="info")
    parser.add_argument("--statsupdateinterval", type=int, default=None)
    args = parser.parse_args()

    configs = yaml.load(open(args.config, "r"))

    configLogFile = configs["log_file"] if "log_file" in configs else None
    logFile = args.log if args.log else configLogFile
    loglevel = {'info':logging.INFO, 'debug':logging.DEBUG}[args.loglevel]
    if logFile:
      logging.basicConfig(filename=logFile, level=loglevel)
    else:
      logging.basicConfig(level=loglevel)
    self.logger = logging

    nrfConfigs = configs["nrf"]
    recAddrPlsize = readPipes(nrfConfigs["pipes"])

    self.statusUpdateIntervalMins = 10  # default
    if "stats_update_interval" in configs: self.statusUpdateIntervalMins = configs["stats_update_interval"]
    if args.statsupdateinterval: self.statusUpdateIntervalMins = args.statsupdateinterval

    try:
      if args.platform == "arietta":
        import spi_intf_arietta
        from spibus import Spibus
        from ablib import Pin
        hardware_intf = spi_intf_arietta.SpiIntfArietta(
          spiBus=Spibus(device="/dev/spidev32766.0", readMode=struct.pack('I',0), writeMode=struct.pack('I',0)),
          cePin = Pin('J4.26','OUTPUT')
        )
        polling = True
      elif args.platform == "rpi":
        import spi_intf_rpi
        import spi
        import RPi.GPIO as GPIO
        hardware_intf = spi_intf_rpi.SpiIntfRPi(spi, GPIO, 25)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(24, GPIO.IN)
        GPIO.add_event_detect(24, GPIO.FALLING, callback=self.readDataIn)
        polling = False


      self.nrf = nrf24L01p.Nrf(
        hardwareIntf = hardware_intf,
        recAddrPlsize=recAddrPlsize,
        channel=nrfConfigs["channel"],
        logger=self.logger,
        crcBytes=nrfConfigs["crcBites"],
        speed=nrfConfigs["speed"])
      self.nrf.clearRx();
      self.nrf.clearStatus();
      self.nrf.clearRx();
      self.nrf.clearStatus();

      self.sender = \
        kiot.KiotSender(
          configs["carbon"]["server"],
          configs["carbon"]["port"],
          configs["graphite_paths"],
          self.logger)

      self.stats = {}
      self.logger.info("Initialization completed, starting to run now, polling mode " + str(polling))

      startTime = time.time()

      while True:
        if polling:
          self.readDataIn()
          if (time.time() - startTime) > self.statusUpdateIntervalMins*60*1000:
            startTime = time.time()
            self.processStats()
        else:
          time.sleep(self.statusUpdateIntervalMins * 60)
          self.processStats()

    finally:
      if polling==False:
        GPIO.remove_event_detect(24)


  def readDataIn(self, channel):
    try:
      data = self.nrf.read()
      if data:
        for datum in data:
          sourceIndex, payload = datum
          packet = kiot.parseKiotPayload(payload)
          if packet.dataIndex in self.stats:
            self.stats[packet.dataIndex] += 1
          else:
            self.stats[packet.dataIndex] = 1
          self.sender.send(packet.dataIndex, packet.dataValue, packet.previousRetryCount)

    except Exception as e:
      self.logger.error(("Error reading packets\n" + traceback.format_exc()))

  def processStats(self):
    try:
      totalCount = 0
      maxCount = 0
      for idx, count in self.stats.iteritems():
        totalCount += count
        if count > maxCount: maxCount = count
      if maxCount==0:
        self.logger.info("Not data for the last %d minute(s). " % self.statusUpdateIntervalMins)
      else:
        self.logger.info("Processed %d packets for %d stats in the last %d minute(s). "
                         "Max update rate: %.0f secs/update",
                         totalCount,
                         len(list(self.stats.iterkeys())),
                         self.statusUpdateIntervalMins,
                         self.statusUpdateIntervalMins * 60 / maxCount
                         )
      self.stats = {}
    except Exception as e:
      self.logger.error(("Error logging stats\n" + traceback.format_exc()))

def readPipes(yamlPipes):
  nrfPipes = []
  for pipe in yamlPipes:
    payloadSize = pipe["size"]
    payloadSize = payloadSize if payloadSize > 0 else None
    pipeAddressString = pipe["address"]
    pipeAddress = [int("0x"+pipeAddressString[i:i+2], 0) for i in range(0, len(pipeAddressString), 2)]
    newPipe = nrf24L01p.NrfPipe(address=pipeAddress, payloadSize=payloadSize)
    nrfPipes.append(newPipe)
  return nrfPipes

if __name__ == '__main__':
  Graphiter().run()
