from nrf24L01p import NrfPipe

def addNrfArgs(parser):
  parser.add_argument('-c', '--channel', default=0x04)
  parser.add_argument('--crc', type=int, default=1)
  parser.add_argument('--speed', type=int, default=0)
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


