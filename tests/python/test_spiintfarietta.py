#!/usr/bin/env python

"""
  To test:
    export PYTHONPATH=$PYTHONPATH:../../src/python/
    ./test_spiintfarietta.py
"""

import unittest
import ctypes
import spi_intf_arietta
from mock import MagicMock


class TestSpiIntfArietta(unittest.TestCase):

  def setUp(self):
    self.mockSpibus = MagicMock()
    self.mockSpibus.read_buffer = ctypes.create_string_buffer(50)
    self.spiIntfArietta = spi_intf_arietta.SpiIntfArietta(self.mockSpibus, 'J4.26')

  def testTransferOutOneScalar(self):
    self.spiIntfArietta.transfer(chr(0x41), 0)
    self.mockSpibus.write_buffer.__setitem__.called_with(0, chr(0x41))
    self.mockSpibus.send.assert_called_with(1)

  def testTransferOutOneList(self):
    self.spiIntfArietta.transfer("".join([chr(0x41)]), 0)
    self.mockSpibus.write_buffer.__setitem__.called_with(0, chr(0x41))
    self.mockSpibus.send.assert_called_with(1)

  def testTransferOutTwo(self):
    self.spiIntfArietta.transfer("".join([chr(0x41), chr(0x42)]), 0)
    self.mockSpibus.write_buffer.__setitem__.called_with(0, chr(0x41))
    self.mockSpibus.write_buffer.__setitem__.called_with(1, chr(0x42))
    self.mockSpibus.send.assert_called_with(2)

  def testTransferOutString(self):
    self.spiIntfArietta.transfer("AB")
    self.mockSpibus.write_buffer.__setitem__.called_with(0, chr(0x41))
    self.mockSpibus.write_buffer.__setitem__.called_with(1, chr(0x42))
    self.mockSpibus.send.assert_called_with(2)

  def testTransferOutOneScalarInOne(self):
    self.mockSpibus.read_buffer[0] = chr(0x43)
    result = self.spiIntfArietta.transfer(chr(0x41), 1)
    self.mockSpibus.write_buffer.__setitem__.called_with(0, chr(0x41))
    self.mockSpibus.send.assert_called_with(1)
    self.assertEquals(result, "".join([chr(0x43)]))

  def testTransferOutOneScalarInTwo(self):
    self.mockSpibus.read_buffer[0] = chr(0x43)
    self.mockSpibus.read_buffer[1] = chr(0x44)
    result = self.spiIntfArietta.transfer(chr(0x41), 2)
    self.mockSpibus.write_buffer.__setitem__.called_with(0, chr(0x41))
    self.mockSpibus.send.assert_called_with(2)
    self.assertEquals(result, "".join([chr(0x43), chr(0x44)]))

if __name__ == '__main__':
  unittest.main()