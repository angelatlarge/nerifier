from struct import *
import socket
import time
import log_thunks

class KiotPacket():
  def __init__(self, dataIndex, dataType, dataTypeDescription, dataValue):
    self.dataIndex = dataIndex
    self.dataType = dataType
    self.dataTypeDescription = dataTypeDescription
    self.dataValue = dataValue


def parseKiotPayload(data):
    (dataIndex, dataType) = unpack('BB', data[0:2])
    if dataType == 3:
      # unsigned 32-bit int
      dataValue = unpack('!l', data[4:8])[0]
      dataDescription = "32-bit uint"
    elif dataType == 5:
      # String
      dataValue = unpack('s', data[4:])[0]
      dataDescription = "string"
    elif dataType == 7:
      # FLoat
      dataValue = unpack('f', data[4:8])[0]
      dataDescription = "float"
    else:
      raise Exception("Unknown data type %d" % (dataType))

    return KiotPacket(dataIndex, dataType, dataDescription, dataValue)

class KiotSender():

  def __init__(self, carbonServer, carbonPort, graphite_paths, logger = log_thunks.FakeLogger):
    self.carbonServer = carbonServer
    self.carbonPort = carbonPort
    self.graphite_paths = graphite_paths
    self.logger = log_thunks.NoLogger if logger == None else logger

  def send(self, dataIndex, dataValue):
    graphitePath = self.graphite_paths[dataIndex]
    message = '%s %s %d' % (graphitePath, str(dataValue), int(time.time()))
    self.logger.info('sending message: %s' % message)
    sock = socket.socket()
    try:
      sock.connect((self.carbonServer, self.carbonPort))
      sock.sendall(message + "\n")
    finally:
      sock.close()


