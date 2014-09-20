#!/usr/bin/env python

import unittest
from nrf24L01p import Nrf
from mock import MagicMock, call

class TestNrf(unittest.TestCase):

  def setUp(self):
    self.seq = range(10)
    self.hardware = MagicMock()
    self.nrf = Nrf(hardwareIntf = self.hardware)

  def testInitilizeRegister(self):
    pass

  def doRegisterWriteTest(self, registerAddress, registerData):
    self.hardware.reset_mock()
    self.nrf.writeRegister(registerAddress, registerData)

    regAddressCall = call(0, registerAddress)
    dataCalls = []
    registerData = registerData if hasattr(registerData, "__len__") else [registerData]
    for i in range(len(registerData)):
      datum = registerData[i]
      index = len(registerData) - i
      dataCalls.append(call(index, datum))

    self.hardware.transfer.called_with([regAddressCall] + dataCalls)
      .write_buffer.__setitem__.called_with()
    self.mockSpibus.send.assert_called_with(len(registerData)+1)

  def testWriteRegister(self):
    self.doRegisterWriteTest(0x04, 0x05)
    self.doRegisterWriteTest(0x01, [0x02, 0x03])


if __name__ == '__main__':
  unittest.main()