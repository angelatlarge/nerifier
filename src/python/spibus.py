import posix
import struct
from ctypes import addressof, create_string_buffer, sizeof, string_at
from fcntl import ioctl
from spi_ctypes import *
import time

class Spibus():
	fd=None
	write_buffer=create_string_buffer(50)
	read_buffer=create_string_buffer(50)

	ioctl_arg = spi_ioc_transfer(
		tx_buf=addressof(write_buffer),
		rx_buf=addressof(read_buffer),
		len=1,
		delay_usecs=100,
		speed_hz=1000000,
		bits_per_word=8,
		cs_change = 1,
	)

	def __init__(self,device="/dev/spidev32766.0",readMode=" ", writeMode=struct.pack('I',0)):
		self.fd = posix.open(device, posix.O_RDWR)
		ioctl(self.fd, SPI_IOC_RD_MODE, readMode)
		ioctl(self.fd, SPI_IOC_WR_MODE, writeMode)

	def send(self,len):
		self.ioctl_arg.len=len
		ioctl(self.fd, SPI_IOC_MESSAGE(1),addressof(self.ioctl_arg))
