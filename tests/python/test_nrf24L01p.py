#!/usr/bin/env python

"""
  To test:
    export PYTHONPATH=$PYTHONPATH:../../src/python/
    ./test_nrf24L01p.py
"""
import unittest
from nrf24L01p import Nrf
from mock import MagicMock, ANY

class ExactLengthMatcher(object):
  def __init__(self, expectedLength):
    self.expectedLength = expectedLength

  def __eq__(self, other):
    return len(other) == self.expectedLength


class TestNrf(unittest.TestCase):

  def setUp(self):
    self.hardware = MagicMock()
    self.hardware.transfer()
    self.nrf = Nrf(hardwareIntf = self.hardware)

  def testWriteRegisterChars(self):
    self.doRegisterWriteTest(0x04, chr(0x05))
    self.doRegisterWriteTest(0x01, [chr(0x02), chr(0x03)])

  def testWriteRegisterBytes(self):
    self.doRegisterWriteTest(0x04, 0x05)
    self.doRegisterWriteTest(0x01, [0x02, 0x03])

  def testCommandList(self):
    self.doCommandTest(0xFF, 0, [chr(0xAA)], None)

  def testCommandString(self):
    self.doCommandTest(0xFF, 0, "A", None)

  def testCommandReturnOne(self):
    self.doCommandTest(0xFF, 1, "AB", "B")

  def testCommandReturnTwo(self):
    self.doCommandTest(0xFF, 2, "ABC", "CB")

  def testReadRegisterOne(self):
    self.doReadRegisterTest(0x08, 1, "_B", "B")

  def testReadRegisterTwo(self):
    self.doReadRegisterTest(0x08, 2, "_BC", "CB")

  def testReadRegisterThree(self):
    self.doReadRegisterTest(0x08, 3, "_BCD", "DCB")

  def testStatus(self):
    self.hardware.reset_mock()
    self.hardware.transfer.return_value = "A"

    result = self.nrf.status()
    self.assertEquals(result, 65)


  def doRegisterWriteTest(self, registerAddress, registerData):
    self.hardware.reset_mock()
    self.nrf.writeRegister(registerAddress, registerData)

    registerData = registerData if hasattr(registerData, "__len__") else [registerData]
    try:
      registerData = "".join(registerData)
    except TypeError:
      registerData = "".join([chr(b) for b in registerData])

    self.hardware.transfer.called_with(chr(registerAddress) + registerData[::-1])

  def doCommandTest(self, commandWord, returnSize, dataIn, expected = None):
    self.assertTrue(len(dataIn) >= returnSize)
    self.hardware.reset_mock()
    self.hardware.transfer.return_value = dataIn

    result = self.nrf.command(commandWord, returnSize)

    self.hardware.transfer.assert_called_with(ANY, returnSize + 1)
    self.assertEquals(result, expected)

  def doReadRegisterTest(self, registerNum, returnSize, dataIn, expected):
    self.assertTrue(returnSize>0, "Internal test failure")
    self.assertEquals(len(dataIn), returnSize+1, "Internal test failure")
    self.assertEquals(len(expected), returnSize, "Internal test failure")

    self.hardware.reset_mock()
    self.hardware.transfer.return_value = dataIn

    result = self.nrf.readRegister(registerNum, returnSize)
    self.hardware.transfer.assert_called_with(ExactLengthMatcher(1), returnSize+1)
    self.assertEquals(result, expected)

if __name__ == '__main__':
  unittest.main()