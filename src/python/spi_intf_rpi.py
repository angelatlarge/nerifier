class SpiIntfRPi:
  def __init__(self, spi, GPIO, cePin = 25):
    self.spi = spi
    self.spi.openSPI()
    self.cePin = cePin
    self.GPIO = GPIO
    self.GPIO.setmode(GPIO.BCM)
    self.GPIO.setup(self.cePin, GPIO.OUT)

  def transfer(self, outData, returnSize = None):
    if returnSize == None: returnSize = len(outData)
    dataList = outData if hasattr(outData, '__len__') else [outData]
    if len(dataList) < returnSize:
      dataList += chr(0) * (returnSize - len(dataList))
    results = self.spi.transfer(tuple((ord(c) for c in dataList)))
    if returnSize == 0:
      return None
    else:
      return "".join([ chr(byte) for byte in results[:returnSize] ])

  def ceLow(self):
    self.GPIO.output(self.cePin, False)

  def ceHigh(self):
    self.GPIO.output(self.cePin, True)

