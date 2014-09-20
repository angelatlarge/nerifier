#!/usr/bin/env python

"""
  To test:
    export PYTHONPATH=$PYTHONPATH:../../src/python/
    ./test_nrf24L01p.py
"""
import unittest
from nrf24L01p import Nrf
from mock import MagicMock

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

  def testCommandWithoutReturn(self):
    self.doCommandTest(0xFF, 0, [chr(0xAA)])

  def testCommandWithReturn(self):
    self.doCommandTest(0xFF, 1, "".join([chr(0x41)]))
    self.doCommandTest(0xFF, 2, "".join([chr(0x41), chr(0x42)]))

  def testReadRegisterOne(self):
    self.doReadRegisterTest(0x08, 1, "AB", "B")

  def testReadRegisterTwo(self):
    self.doReadRegisterTest(0x08, 1, "ABC", "CB")

  def doRegisterWriteTest(self, registerAddress, registerData):
    self.hardware.reset_mock()
    self.nrf.writeRegister(registerAddress, registerData)

    registerData = registerData if hasattr(registerData, "__len__") else [registerData]
    try:
      registerData = "".join(registerData)
    except TypeError:
      registerData = "".join([chr(b) for b in registerData])

    self.hardware.transfer.called_with(chr(registerAddress) + registerData[::-1])

  def doCommandTest(self, commandWord, returnSize, dataIn):
    self.assertTrue(len(dataIn) >= returnSize)
    self.hardware.reset_mock()
    self.hardware.transfer.return_value = dataIn

    result = self.nrf.command(commandWord, returnSize)

    self.hardware.transfer.called_with(chr(commandWord), returnSize)
    if returnSize == 0:
      self.assertIsNone(result)
    else:
      self.assertEquals(result, dataIn[1:][::-1])

  def doReadRegisterTest(self, registerNum, returnSize, dataIn, expected):
    self.hardware.reset_mock()
    self.hardware.transfer.return_value = dataIn

    result = self.nrf.readRegister(registerNum, returnSize)
    self.assertEquals(result, expected)


if __name__ == '__main__':
  unittest.main()