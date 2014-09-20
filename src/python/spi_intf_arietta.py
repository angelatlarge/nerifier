
class SpiIntfArietta:
  def __init__(self, spiBus, cePin):
    self.spibus = spiBus
    self.cePin = cePin

  def transfer(self, outData, returnSize = None):
    if returnSize == None: returnSize = len(outData)
    dataList = outData if hasattr(outData, '__len__') else [outData]
    for idx in range(len(dataList)):
      self.spibus.write_buffer[idx] = dataList[idx]
    self.spibus.send(max(len(dataList), returnSize))
    return self.spibus.read_buffer[:returnSize]

  def ceLow(self):
    self.cePin.low()

  def ceHigh(self):
    self.cePin.high()
