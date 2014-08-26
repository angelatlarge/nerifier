import struct
import random
from spibus import Spibus
from ablib import Pin

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
  return " ".join(("%0X" % byte for byte in addr))


class Nrf():
  
  def __init__(
      self,
      addressWidth = 5,
      recAddrPlsize = (0x25, None),
      spiDevice="/dev/spidev32766.0",
      cePinId='J4.26',
      channel = 2,
      speed = 0,
      autoRetransmitCount = 15,
      autoRetransmitDelay = random.randrange(16),
      crcScheme = 0
  ):
    """
      addressWidth        the number of bytes used for the address. Legal values are 3, 4, and 5
      recAddrPayload      Tuple (or a list of tuples up to 6 elements long) of receiver address and payload size
      spiDevice           Path to the device on your system
      cdPinId             Name of the GPIO pin connected to the CE pin of NRF24L01 plus
      crcScheme
      autoRetransmitBits
    """
    self.cePin = Pin(cePinId,'OUTPUT')


    self.cePin.low()  # Xmit off

    # Initialize the SPI bus
    self.spibus = Spibus(device=spiDevice, readMode=struct.pack('I',0), writeMode=struct.pack('I',0))

    # Set address width: convert as follows 3->1, 4->2, 5>3
    self.addressWidth = min(5, addressWidth)
    self.writeRegister(Reg.SETUP_AW, self.addressWidth - 2)

    # Set up the CRC scheme
    self.crcBits = 0 if not crcScheme else 1<<Bits.EN_CRC | (min(crcScheme, 1) << Bits.CRCO)

    # Set up auto retransmit delay and count
    self.writeRegister(Reg.SETUP_RETR, min(autoRetransmitDelay, 15) << 4 | min(autoRetransmitCount, 15))

    # Set up the channel
    self.writeRegister(Reg.RF_CH, min(63, channel))

    # Set up the speed
    self.writeRegister(Reg.RF_SETUP, 0x03 << 1)
    # self.writeRegister(Reg.RF_SETUP, 0x26)


    # set up payload sizes
    if recAddrPlsize:

      # Convert recAddrPayload into a list
      self.recAddrPayload = recAddrPlsize[0:6] if isinstance(recAddrPlsize, list) else [recAddrPlsize]

      # Enable dynamic payload if necessary
      dynamicPayloadSizeBit = 1 if any([not size for (addr, size) in self.recAddrPayload]) else 0
      self.writeRegister(Reg.FEATURE, (dynamicPayloadSizeBit << Bits.EN_DPL | 1<<Bits.EN_ACK_PAY | 0<<Bits.EN_DYN_ACK))

      # Set payload sizes
      pipesEnableValue = 0
      autoAckValue = 0
      dynamicPayloadSizePipes = 0
      for idx,(addr, size) in enumerate(self.recAddrPayload):
        # Enable pipe
        print "Enabling pipe %d" % (idx)
        pipesEnableValue |= 1<<idx

        # Enable auto ack
        autoAckValue |= 1<<idx

        # Set receive address
        print "Retting recieve address for pipe %d to %s" % (idx, printBinary(addr))
        self.writeRegister(Reg.RX_ADDR_P0+idx, addr)

        # Set payload size
        if size:
          writtenSize = max(1, min(size, 32))
          print "Setting payload size %d for pipe %d" % (writtenSize, idx)
          self.writeRegister(Reg.RX_PW_P0+idx, writtenSize)
        else:
          print "Using dynamic payload size for pipe %d" % (writtenSize, idx)
          dynamicPayloadSizePipes |= 1<<idx

      # Write dynamic payload size
      self.writeRegister(Reg.DYNPD, dynamicPayloadSizePipes)

      # Write pipes enable
      self.writeRegister(Reg.EN_RXADDR, pipesEnableValue)

      # Write auto-acking
      self.writeRegister(Reg.EN_AA, autoAckValue)

    self.writeRegister(Reg.STATUS,(1<<Bits.RX_DR)|(1<<Bits.TX_DS)|(1<<Bits.MAX_RT));
    # Default receive mode
    self.writeRegister(Reg.CONFIG, self.crcBits|((1<<Bits.PWR_UP)|(1<<Bits.PRIM_RX)));

    self.cePin.high() # ???

  def readRegister(self, register, size=1):
    return self.command(chr(Cmd.R_REGISTER | (REGISTER_MASK & register)), size)

  def writeRegister(self, register, data):
    self.spibus.write_buffer[0] = chr(Cmd.W_REGISTER | (REGISTER_MASK & register))
    dataList = data if hasattr(data, '__len__') else [data]
    for idx in range(len(dataList)):
      self.spibus.write_buffer[len(dataList)-idx] = chr(dataList[idx])
    self.spibus.send(len(dataList)+1)

  def command(self, commandBits, returnSize = 0):
    self.spibus.write_buffer[0] = chr(commandBits)
    self.spibus.write_buffer[1] = chr(0)
    self.spibus.send(1+returnSize)
    if returnSize > 0:
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

  def read(self):
    if self.recAddrPayload:
      availablePipeIndex = self.status() & Bits.RX_P_NO_MASK
      if (availablePipeIndex != RX_FIFO_EMPTY):
        availablePipeIndex >>= 1;
        if availablePipeIndex>=len(self.recAddrPayload):
          raise Exception("Invalid availablePipeIndex %d", availablePipeIndex)
        payloadSize = self.recAddrPayload[availablePipeIndex][1];
        payloadSize = payloadSize if payloadSize else self.command(Cmd.R_RX_PL_WID, 1).next()
        data = self.command(Cmd.R_RX_PAYLOAD, payloadSize)
        return (availablePipeIndex, data)
    return None
