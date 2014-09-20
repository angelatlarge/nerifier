from struct import *
import socket
import time
import log_thunks

class KiotPacket():
  def __init__(self, dataIndex, dataType, dataTypeDescription, dataValue, previousRetryCount):
    self.dataIndex = dataIndex
    self.dataType = dataType
    self.dataTypeDescription = dataTypeDescription
    self.dataValue = dataValue
    self.previousRetryCount = previousRetryCount


def parseKiotPayload(data):
    (dataIndex, dataType, prevRetryCount) = unpack('!BBH', data[0:4])
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

    return KiotPacket(dataIndex, dataType, dataDescription, dataValue, prevRetryCount)

class KiotSender():

  def __init__(self, carbonServer, carbonPort, graphite_paths, logger = log_thunks.FakeLogger):
    self.carbonServer = carbonServer
    self.carbonPort = carbonPort
    self.graphite_paths = graphite_paths
    self.logger = log_thunks.NoLogger if logger == None else logger

  def send(self, dataIndex, dataValue, retryCount):
    graphitePath = self.graphite_paths[dataIndex]
    timestamp = int(time.time())
    metricMessage = '%s.value %s %d' % (graphitePath, str(dataValue), timestamp)
    retryMessage = '%s.retries %d %d' % (graphitePath, retryCount, timestamp)
    self.sendMessage(metricMessage)
    self.sendMessage(retryMessage)

  def sendMessage(self, message):
    self.logger.info('sending message: %s' % message)
    sock = socket.socket()
    try:
      sock.connect((self.carbonServer, self.carbonPort))
      sock.sendall(message + "\n")
    finally:
      sock.close()


