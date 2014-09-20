#!/usr/bin/env python

import argparse
import yaml
import nrf24L01p
import kiot
import logging
import struct

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('platform', choices=['arietta', 'rpi'])
  parser.add_argument("-c", "--config", type=str, default="nrfconfig.yaml")
  parser.add_argument("-l", "--log", type=str)
  args = parser.parse_args()

  configs = yaml.load(open(args.config, "r"))

  configLogFile = configs["log_file"] if "log_file" in configs else None
  logFile = args.log if args.log else configLogFile
  # logger = logging if not configs["log_file"] else logging.basicConfig(filename=configs["log_file"],level=logging.INFO)
  if logFile:
    logging.basicConfig(filename=logFile, level=logging.INFO)
  else:
    logging.basicConfig(level=logging.INFO)
  logger = logging

  nrfConfigs = configs["nrf"]
  recAddrPlsize = readPipes(nrfConfigs["pipes"])

  if args.platform == "arietta":
    import spi_intf_arietta
    from spibus import Spibus
    from ablib import Pin
    hardware_intf = spi_intf_arietta.SpiIntfArietta(
      spiBus=Spibus(device="/dev/spidev32766.0", readMode=struct.pack('I',0), writeMode=struct.pack('I',0)),
      cePin = Pin('J4.26','OUTPUT')
    )
  elif args.platform == "rpi":
    import spi_intf_rpi
    import spi
    import RPi.GPIO as GPIO
    hardware_intf = spi_intf_rpi.SpiIntfRPi(spi, GPIO, 25)

  nrf = nrf24L01p.Nrf(
    hardwareIntf = hardware_intf,
    recAddrPlsize=recAddrPlsize,
    channel=nrfConfigs["channel"],
    logger=logger,
    crcBytes=nrfConfigs["crcBites"],
    speed=nrfConfigs["speed"])
  nrf.clearRx();
  nrf.clearStatus();
  nrf.clearRx();
  nrf.clearStatus();

  sender = kiot.KiotSender(configs["carbon"]["server"], configs["carbon"]["port"], configs["graphite_paths"], logger)

  while True:
    data = nrf.read()
    for datum in data:
      sourceIndex, payload = datum
      try:
        packet = kiot.parseKiotPayload(payload)
        sender.send(packet.dataIndex, packet.dataValue, packet.previousRetryCount)
      except Exception as e:
        logger.error(("Error processing packet \n", e))


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
  main()
