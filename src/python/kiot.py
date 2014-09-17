from struct import *
import socket
import time
import traceback

class KiotPacket():
  def __init__(self, dataIndex, dataType, dataTypeDescription, dataValue):
    self.dataIndex = dataIndex
    self.dataType = dataType
    self.dataTypeDescription = dataTypeDescription
    self.dataValue = dataValue

def parseKiotPayload(data):
  try:
    (dataIndex, dataType) = unpack('BB', data[0:2])
    if dataType == 3:
      # unsigned 32-bit int
      dataValue = unpack('!l', data[4:8])[0]
      dataDescription = "32-bit uint"
    elif dataType == 5:
      # String
      dataValue = unpack('s', data[4:])[0]
      dataDescription = "string"
    else:
      raise Exception("Unknown data type %d" % (dataType))
    return KiotPacket(dataIndex, dataType, dataDescription, dataValue)
  except Exception as e: print "Failed to parse packet", e, traceback.print_exc()
  return None

class KiotSender():

  def __init__(self, carbonServer, carbonPort, graphite_paths):
    self.carbonServer = carbonServer
    self.carbonPort = carbonPort
    self.graphite_paths = graphite_paths

  def send(self, dataIndex, dataValue):
    try:
      graphitePath = self.graphite_paths[dataIndex]
      message = '%s %s %d' % (graphitePath, str(dataValue), int(time.time()))
      print 'sending message: %s' % message,
      sock = socket.socket()
      try:
        sock.connect((self.carbonServer, self.carbonPort))
        sock.sendall(message + "\n")
        print "...sent",
      finally:
        print ""
        sock.close()
    except Exception as e: print "Failed to send data to graphite", e, traceback.print_exc()


