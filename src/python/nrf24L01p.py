import struct
import random
from spibus import Spibus
from ablib import Pin
from time import sleep

# Commands
class Cmd:
  R_REGISTER          = 0x00 # last 4 bits will indicate reg. address
  W_REGISTER          = 0x20 # last 4 bits will indicate reg. address
  R_RX_PAYLOAD        = 0x61
  W_TX_PAYLOAD        = 0xA0
  FLUSH_TX            = 0xE1
  FLUSH_RX            = 0xE2
  REUSE_TX_PL         = 0xE3
  R_RX_PL_WID         = 0x60
  W_ACK_PAYLOAD       = 0xA8
  W_TX_PAYLOAD_NOACK  = 0x58
  NOP                 = 0xFF

class Reg:
  # Registers
  CONFIG              = 0x00
  EN_AA               = 0x01
  EN_RXADDR           = 0x02
  SETUP_AW            = 0x03
  SETUP_RETR          = 0x04
  RF_CH               = 0x05
  RF_SETUP            = 0x06
  STATUS              = 0x07
  OBSERVE_TX          = 0x08
  RPD                 = 0x09 # formerly "CD"
  RX_ADDR_P0          = 0x0A
  RX_ADDR_P1          = 0x0B
  RX_ADDR_P2          = 0x0C
  RX_ADDR_P3          = 0x0D
  RX_ADDR_P4          = 0x0E
  RX_ADDR_P5          = 0x0F
  TX_ADDR             = 0x10
  RX_PW_P0            = 0x11
  RX_PW_P1            = 0x12
  RX_PW_P2            = 0x13
  RX_PW_P3            = 0x14
  RX_PW_P4            = 0x15
  RX_PW_P5            = 0x16
  FIFO_STATUS         = 0x17
  DYNPD               = 0x1C
  FEATURE             = 0x1D

# Bit Mnemonics
class Bits:
  # configuratio nregister
  MASK_RX_DR          = 6
  MASK_TX_DS          = 5
  MASK_MAX_RT         = 4
  EN_CRC              = 3
  CRCO                = 2
  PWR_UP              = 1
  PRIM_RX             = 0
  
  # setup of address width
  #define AW          0 /* 2 bits */
  
  # setup of auto re-transmission
  #define ARD         4 /* 4 bits */
  #define ARC         0 /* 4 bits */
  
  # RF setup register
  #define PLL_LOCK    4
  #define RF_DR       3
  #define RF_PWR      1 /* 2 bits */
  
  # general status register
  RX_DR               = 6
  TX_DS               = 5
  MAX_RT              = 4
  RX_P_NO             = 1 # 3 bits
  RX_P_NO_MASK        = 0x0E
  TX_FULL             = 0
  
  # transmit observe register
  #define PLOS_CNT    4 /* 4 bits */
  #define ARC_CNT     0 /* 4 bits */
  
  # fifo status
  #define TX_REUSE    6
  #define FIFO_FULL   5
  #define TX_EMPTY    4
  #define RX_FULL     1
  #define RX_EMPTY    0
  
  # dynamic length
  #define DPL_P0      0
  #define DPL_P1      1
  #define DPL_P2      2
  #define DPL_P3      3
  #define DPL_P4      4
  #define DPL_P5      5
  
  # Feature register bits
  EN_DPL          = 2
  EN_ACK_PAY      = 1
  EN_DYN_ACK      = 0


REGISTER_MASK           = 0x1F
RX_FIFO_EMPTY           = Bits.RX_P_NO_MASK


def printBinary(addr):
  addr = addr if isinstance(addr, list) else [addr]
  return " ".join(("%0X" % byte for byte in addr))

class NrfPipe():
  def __init__(self, address = None, payloadSize = None):
    self._address = address
    self._payloadSize = payloadSize

  @property
  def address(self):
    return self._address

  @property
  def payloadSize(self):
    return self._payloadSize

  def __str__(self):
    return "NrfPipe(address=%s, payloadSize=%s)" % (self._address, self._payloadSize)

  __repr__ = __str__

class Nrf():

  """
    addressWidth        the number of bytes used for the address. Legal values are 3, 4, and 5
    recAddrPayload      Tuple (or a list of tuples up to 6 elements long) of receiver address and payload size
    spiDevice           Path to the device on your system
    cdPinId             Name of the GPIO pin connected to the CE pin of NRF24L01 plus
    crcScheme
    autoRetransmitBits
  """
  def __init__(
      self,
      spiBus = None,
      addressWidth = 5,
      recAddrPlsize = [NrfPipe(None, 4)],
      cePinId='J4.26',
      channel = 2,
      speed = 0,
      autoRetransmitCount = 15,
      autoRetransmitDelay = random.randrange(16),
      crcScheme = 0
  ):
    self.cePin = Pin(cePinId,'OUTPUT')


    self.cePin.low()  # Xmit off

    print("Sleeping for one sec..."),
    sleep(1)
    print("done")

    # Initialize the SPI bus
    self.spibus = Spibus(device="/dev/spidev32766.0", readMode=struct.pack('I',0), writeMode=struct.pack('I',0)) if spiBus == None else spiBus

    # Power up the chip, put it into TX mode
    self.writeRegister(Reg.CONFIG, 1<<Bits.PWR_UP)

    # Set address width: convert as follows 3->1, 4->2, 5>3
    self.addressWidth = max(min(5, addressWidth), 3)
    self.writeRegister(Reg.SETUP_AW, self.addressWidth - 2)

    # Set up the CRC scheme
    self.crcBits = 0 if crcScheme==None else 1<<Bits.EN_CRC | (min(crcScheme, 1) << Bits.CRCO)

    # Set up auto retransmit delay and count
    # self.writeRegister(Reg.SETUP_RETR, min(autoRetransmitDelay, 15) << 4 | min(autoRetransmitCount, 15))
    self.writeRegister(Reg.SETUP_RETR, 0xFF)

    # Set up the channel
    channel = min(0x7F, channel)
    print( "Writing %02x as the channel" % (channel) )
    self.writeRegister(Reg.RF_CH, channel)

    # Set up the speed
    # self.writeRegister(Reg.RF_SETUP, 0x03 << 1)
    # self.writeRegister(Reg.RF_SETUP, 0x15)
    # self.writeRegister(Reg.RF_SETUP, 0x06)
    # self.writeRegister(Reg.RF_SETUP, 0x26)
    self.writeRegister(Reg.RF_SETUP, 0x0E)


    # set up payload sizes
    print recAddrPlsize
    if recAddrPlsize:

      # Convert recAddrPayload into a list
      self.recAddrPayload = recAddrPlsize[0:6] if isinstance(recAddrPlsize, list) else [recAddrPlsize]

      # Enable dynamic payload if necessary
      print self.recAddrPayload
      dynamicPayloadSizeBit = 1 if any([not pipe.payloadSize for pipe in self.recAddrPayload if pipe]) else 0
      print( "Writing %02x into FEATURE" % (dynamicPayloadSizeBit << Bits.EN_DPL) )
      self.writeRegister(Reg.FEATURE, (dynamicPayloadSizeBit << Bits.EN_DPL))

      # Set payload sizes
      pipesEnableValue = 0
      autoAckValue = 0
      dynamicPayloadSizePipes = 0
      for idx, pipe in enumerate(self.recAddrPayload):
        if pipe==None:
          print "Pipe %d disabled" % (idx)
        else:
          # Enable pipe
          print "Enabling pipe %d" % (idx)
          pipesEnableValue |= 1<<idx

          # Enable auto ack
          autoAckValue |= 1<<idx

          # Set receive address
          if pipe.address:
            print "Setting recieve address for pipe %d to %s" % (idx, printBinary(pipe.address))
            self.writeRegister(Reg.RX_ADDR_P0+idx, pipe.address)
          else:
            print "Pipe address for this pipe remains default"

          # Set payload size
          if pipe.payloadSize:
            writtenSize = max(1, min(pipe.payloadSize, 32))
            print "Setting payload size %d for pipe %d" % (writtenSize, idx)
            self.writeRegister(Reg.RX_PW_P0+idx, writtenSize)
          else:
            print "Using dynamic payload size for pipe %d" % (idx)
            dynamicPayloadSizePipes |= 1<<idx

      # Write dynamic payload size
      print( "Writing %02x into DYNPD" % (dynamicPayloadSizePipes) )
      self.writeRegister(Reg.DYNPD, dynamicPayloadSizePipes)

      # Write pipes enable
      pipesEnableValue = 3
      print( "Writing %02x into EN_RXADDR" % (pipesEnableValue) )
      self.writeRegister(Reg.EN_RXADDR, pipesEnableValue)

      # Write auto-acking
      self.writeRegister(Reg.EN_AA, autoAckValue)

    self.writeRegister(Reg.EN_AA, 0x3F)

    # Set to receive mode
    self.writeRegister(Reg.CONFIG, self.crcBits|((1<<Bits.PWR_UP)|(1<<Bits.PRIM_RX)));

    self.cePin.high() # Necessary for RX mode

  def readRegister(self, register, size=1):
    return self.command(Cmd.R_REGISTER | (REGISTER_MASK & register), size)

  def writeRegister(self, register, data):
    self.spibus.write_buffer[0] = chr(Cmd.W_REGISTER | (REGISTER_MASK & register))
    dataList = data if hasattr(data, '__len__') else [data]
    for idx in range(len(dataList)):
      self.spibus.write_buffer[len(dataList)-idx] = chr(dataList[idx])
    self.spibus.send(len(dataList)+1)

  def command(self, commandBits, returnSize = 0):
    self.spibus.write_buffer[0] = chr(commandBits)

    # Testing initialization
    for i in range(returnSize+1):
      self.spibus.read_buffer[i] = chr(0xFF)

    self.spibus.send(1+returnSize)
    if returnSize > 0:
      # return (ord(self.spibus.read_buffer[idx+1]) for idx in range(returnSize))
      # return (ord(self.spibus.read_buffer[idx]) for idx in range(returnSize))
      return (ord(self.spibus.read_buffer[returnSize-idx]) for idx in range(returnSize))

  def powerUpTx(self):
    self.nrf24_writeRegister(Reg.STATUS,(1<<Bits.RX_DR)|(1<<self.BOT_TX_DS)|(1<<Bits.MAX_RT));
    self.nrf24_writeRegister(Reg.CONFIG, self.crcBits|((1<<Bits.PWR_UP)|(0<<Bits.PRIM_RX)));

  def send(self, data):
    """ Need to try to unify this with writeRegister, and command()
    """
    self.cePin.low()
    self.powerUpTx()
    self.command(Cmd.FLUSH_TX)
    self.spibus.write_buffer[0] = Cmd.W_TX_PAYLOAD
    for idx in len(data):
      self.spibus.write_buffer[len(data)-idx] = chr(data[idx])
    self.spibus.send(len(data))
    self.cePin.high()

  def status(self):
    """ Status is sent back while the command is being sent there """
    self.spibus.write_buffer[0] = chr(Cmd.NOP)
    self.spibus.send(1)
    return (ord(self.spibus.read_buffer[0]))


  def dataReceivedPipeIndex(self, status):
    availablePipeIndex = status & Bits.RX_P_NO_MASK
    if (availablePipeIndex != RX_FIFO_EMPTY):
      return availablePipeIndex >> 1;
    else:
      return None


  def read(self):
    if self.recAddrPayload:
      status = self.status()
      idxPipe = self.dataReceivedPipeIndex(status)
      if (status & (1<<Bits.RX_DR)) or idxPipe != None:
        try:
          if idxPipe == None:
            self.writeRegister(Reg.STATUS, 1<<Bits.RX_DR|1<<Bits.TX_DS|1<<Bits.MASK_MAX_RT)
            raise Exception("Nrf told us there would be data, but could got no pipe index, clearing status")
          if idxPipe>=len(self.recAddrPayload):
            raise Exception("Invalid availablePipeIndex %d", idxPipe)
          pipe = self.recAddrPayload[idxPipe]
          payloadSize = pipe.payloadSize
          print "Specified payload size is ", payloadSize
          if not payloadSize:
            payloadSizeCmdOut = list(self.command(Cmd.R_RX_PL_WID, 1))
            print "Dynamic payload size=", payloadSizeCmdOut
            payloadSize = payloadSizeCmdOut[0]
          if (payloadSize) > 32:
            print "Corrupt data in buffer, flushing"
            # Corrupt packet due to data overflow
            self.command(Cmd.FLUSH_RX)
            return None
          else:
            # Reading payload
            data = self.command(Cmd.R_RX_PAYLOAD, payloadSize)
            self.writeRegister(Reg.STATUS, 0x7F) # clear data received bit
            return (idxPipe, data)
        except Exception as e:
          print str(e)
      else:
        # No data available
        return None
    else:
      raise Exception("self.recAddrPayload misconfigured. Cannot read")
