#!/usr/bin/env python

import argparse
import yaml
import nrf24L01p
import kiot
import logging
import traceback

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("-c", "--config", type=str, default="nrfconfig.yaml")
  args = parser.parse_args()

  configs = yaml.load(open(args.config, "r"))

  logFile = configs["log_file"] if "log_file" in configs else None
  # logger = logging if not configs["log_file"] else logging.basicConfig(filename=configs["log_file"],level=logging.INFO)
  if logFile:
    logging.basicConfig(filename=logFile, level=logging.INFO)
  else:
    logging.basicConfig(level=logging.INFO)
  logger = logging

  recAddrPlsize = readPipes(configs["nrf"]["pipes"])

  nrf = nrf24L01p.Nrf(recAddrPlsize=recAddrPlsize, channel=configs["nrf"]["channel"], logger=logger)
  nrf.clearRx();

  sender = kiot.KiotSender(configs["carbon"]["server"], configs["carbon"]["port"], configs["graphite_paths"], logger)

  while True:
    data = nrf.read()
    if data:
      sourceIndex, payload = data
      try:
        packet = kiot.parseKiotPayload(payload)
        sender.send(packet.dataIndex, packet.dataValue)
      except Exception as e:
        logger.error(("Error processing packet \n%s\n" %(e)) + traceback.print_exc())


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
