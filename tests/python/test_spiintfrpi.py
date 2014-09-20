#!/usr/bin/env python

import unittest
import spi_intf_rpi
from mock import MagicMock

class TestSpiIntfRpi(unittest.TestCase):

  def setUp(self):
    self.mockSpi = MagicMock()
    self.mockGPIO = MagicMock()
    self.spiIntfPRi = spi_intf_rpi.SpiIntfRPi(self.mockSpi, self.mockGPIO)

  def testTransferOutOneScalar(self):
    result = self.spiIntfPRi.transfer(chr(65), 0)
    self.mockSpi.transfer.assert_called_with((65,))
    self.assertEquals(result, None)

  def testTransferOutOneList(self):
    result = self.spiIntfPRi.transfer("".join([chr(65)]), 0)
    self.mockSpi.transfer.assert_called_with((65,))
    self.assertEquals(result, None)

  def testTransferOutTwo(self):
    result = self.spiIntfPRi.transfer("".join([chr(65), chr(66)]), 0)
    self.mockSpi.transfer.assert_called_with((65, 66,))
    self.assertEquals(result, None)

  def testTransferOutString(self):
    result = self.spiIntfPRi.transfer("AB", 0)
    self.mockSpi.transfer.assert_called_with((65, 66,))
    self.assertEquals(result, None)

  def testTransferOutOneScalarInOne(self):
    self.mockSpi.transfer.return_value = (66,)
    result = self.spiIntfPRi.transfer(chr(65), 1)
    self.mockSpi.transfer.assert_called_with((65,))
    self.assertEquals(result, "B")

  def testTransferOutOneScalarInTwo(self):
    self.mockSpi.transfer.return_value = (66,67,)
    result = self.spiIntfPRi.transfer(chr(65), 2)
    self.mockSpi.transfer.assert_called_with((65,0,))
    self.assertEquals(result, "BC")

  def testTransferOutTwoInTwo(self):
    self.mockSpi.transfer.return_value = (67,68,)
    result = self.spiIntfPRi.transfer("AB")
    self.mockSpi.transfer.assert_called_with((65,66,))
    self.assertEquals(result, "CD")

  def testTransferOutTwoInOne(self):
    self.mockSpi.transfer.return_value = (67,68,)
    result = self.spiIntfPRi.transfer("AB", 1)
    self.mockSpi.transfer.assert_called_with((65,66,))
    self.assertEquals(result, "C")

if __name__ == '__main__':
  unittest.main()
