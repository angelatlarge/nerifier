import struct
from spibus import Spibus
from ablib import Pin

class Nrf():
  # Commands
  CMD_R_REGISTER          = 0x00 # last 4 bits will indicate reg. address
  CMD_W_REGISTER          = 0x20 # last 4 bits will indicate reg. address
  CMD_R_RX_PAYLOAD        = 0x61
  CMD_W_TX_PAYLOAD        = 0xA0
  CMD_FLUSH_TX            = 0xE1
  CMD_FLUSH_RX            = 0xE2
  CMD_REUSE_TX_PL         = 0xE3
  CMD_R_RX_PL_WID         = 0x60
  CMD_W_ACK_PAYLOAD       = 0xA8
  CMD_W_TX_PAYLOAD_NOACK  = 0x58
  CMD_NOP                 = 0xFF

  # Registers
  REG_CONFIG       = 0x00
  REG_EN_AA        = 0x01
  REG_EN_RXADDR    = 0x02
  REG_SETUP_AW     = 0x03
  REG_SETUP_RETR   = 0x04
  REG_RF_CH        = 0x05
  REG_RF_SETUP     = 0x06
  REG_STATUS       = 0x07
  REG_OBSERVE_TX   = 0x08
  REG_RPD          = 0x09 # formerly "CD"
  REG_RX_ADDR_P0   = 0x0A
  REG_RX_ADDR_P1   = 0x0B
  REG_RX_ADDR_P2   = 0x0C
  REG_RX_ADDR_P3   = 0x0D
  REG_RX_ADDR_P4   = 0x0E
  REG_RX_ADDR_P5   = 0x0F
  REG_TX_ADDR      = 0x10
  REG_RX_PW_P0     = 0x11
  REG_RX_PW_P1     = 0x12
  REG_RX_PW_P2     = 0x13
  REG_RX_PW_P3     = 0x14
  REG_RX_PW_P4     = 0x15
  REG_RX_PW_P5     = 0x16
  REG_FIFO_STATUS  = 0x17
  REG_DYNPD        = 0x1C
  REG_FEATURE      = 0x1D

  # Bit Mnemonics

  # configuratio nregister
  BIT_MASK_RX_DR    = 6
  BIT_MASK_TX_DS    = 5
  BIT_MASK_MAX_RT   = 4
  BIT_EN_CRC        = 3
  BIT_CRCO          = 2
  BIT_PWR_UP        = 1
  BIT_PRIM_RX       = 0

  # enable auto acknowledgment
  #define ENAA_P5     5
  #define ENAA_P4     4
  #define ENAA_P3     3
  #define ENAA_P2     2
  #define ENAA_P1     1
  #define ENAA_P0     0

  # enable rx addresses
  #define ERX_P5      5
  #define ERX_P4      4
  #define ERX_P3      3
  #define ERX_P2      2
  #define ERX_P1      1
  #define ERX_P0      0

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
  BIT_RX_DR           = 6
  BIT_TX_DS           = 5
  BIT_MAX_RT          = 4
  BIT_RX_P_NO         = 1 # 3 bits
  BIT_TX_FULL         = 0

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
  BIT_EN_DPL          = 2
  BIT_EN_ACK_PAY      = 1
  BIT_EN_DYN_ACK      = 0


  REGISTER_MASK           = 0x1F


  def __init__(self, payloadLength=None, spiDevice="/dev/spidev32766.0", cdPinId='J4.26', crcScheme = 0):
    self.cePin = Pin(cdPinId,'OUTPUT')
    self.cePin.low()
    self.spibus = Spibus(device=spiDevice, readMode=struct.pack('I',0), writeMode=struct.pack('I',0))
    self.nrf24_writeRegister(self.REG_FEATURE, ((1 if self.payloadLength else 0) << self.BIT_EN_DPL | 1<<self.BIT_EN_ACK_PAY | 0<<self.BIT_EN_DYN_ACK))

  def readRegister(self, register, size=1):
    return self.command(chr(self.CMD_R_REGISTER | (self.REGISTER_MASK & register)), size)

  def nrf24_writeRegister(self, register, data):
    self.spibus.write_buffer[0] = chr(self.W_REGISTER | (self.REGISTER_MASK & register))
    dataList = data if hasattr(data, 'len') else [data]
    for idx in range(len(dataList)):
      self.spibus.write_buffer[idx+1] = chr(dataList[idx])
    self.spibus.send(len(dataList+1))

  def command(self, commandBits, returnSize = 0):
    self.spibus.write_buffer[0] = chr(commandBits)
    self.spibus.write_buffer[1] = chr(0)
    self.spibus.send(1+returnSize)
    if returnSize > 0:
      return (ord(self.spibus.read_buffer[idx]) for idx in range(1,returnSize+1))

  def powerUpTx(self):
    self.nrf24_writeRegister(self.REG_STATUS,(1<<self.BIT_RX_DR)|(1<<self.BOT_TX_DS)|(1<<self.BIT_MAX_RT));
    crcVal = 0 if not self.crcScheme else 1<<self.BIT_EN_CRC | (max(self.crcScheme, 1) << self.BIT_CRCO)
    self.nrf24_writeRegister(self.REG_CONFIG, crcVal|((1<<self.BIT_PWR_UP)|(0<<self.BIT_PRIM_RX)));

  def send(self, data):
    self.cePin.low()
    self.powerUpTx()
    self.command(self.CMD_FLUSH_TX)
    for idx in len(data):
      self.spibus.write_buffer[len(data)-idx-1] = chr(data[idx])
    self.spibus.send(len(data))
    self.cePin.high()

  def status(self):
    return self.command(self.CMD_NOP, 1)

  def hasReceivedData(self):
    return self.status & 1 << self.BIT_RX_DR > 0

  def getReceivedData(self):
    dataSize = self.payloadLength if self.payloadLength else self.command(self.CMD_R_RX_PL_WID, 1)
    return self.command(self.CMD_R_RX_PAYLOAD, dataSize)
