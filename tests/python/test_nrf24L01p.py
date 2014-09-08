#!/usr/bin/env python

import unittest
from nrf24L01p import Nrf
from mock import MagicMock

class TestNrf(unittest.TestCase):

  def setUp(self):
    self.seq = range(10)

  def testInitilizeRegister(self):
    spibus = MagicMock()
    nrf = Nrf(spibus)


  def testWriteRegister(self):
    spibus = MagicMock()
    nrf = Nrf(spibus)
    nrf.writeRegister(0x01, [0x02, 0x03])

    spibus.write_buffer.assert_called_with()
    spibus.send.assert_called_with(3)
    print spibus.send.call_args_list
    print spibus.write_buffer.call_args_list
    print spibus.mock_calls

if __name__ == '__main__':
  unittest.main()