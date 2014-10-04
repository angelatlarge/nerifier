class SpiRPi:
  def __init__(self, spi, GPIO, cePin = 25, irqPin = None):
    self.spi = spi
    self.spi.openSPI()
    self.cePin = cePin
    self.GPIO = GPIO
    self.GPIO.setmode(GPIO.BCM)
    self.GPIO.setup(self.cePin, GPIO.OUT)
    self.irqPin = irqPin
    self.irqAttached = False
    if self.irqPin != None:
      GPIO.setup(self.irqPin, GPIO.IN)


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

  def __exit__(self, type, value, traceback):
    self.spi.closeSPI()

  def ceLow(self):
    self.GPIO.output(self.cePin, False)

  def ceHigh(self):
    self.GPIO.output(self.cePin, True)

  @property
  def canAttachIrq(self):
    return self.irqPin != None

  def irqAttach(self, callback):
    self.GPIO.add_event_detect(self.irqPin, self.GPIO.FALLING, callback=callback)
    self.irqAttached = True

  def irqDetach(self):
    if self.irqAttached:
      self.GPIO.remove_event_detect(self.irqPin)
      self.irqAttached = False

  def __enter__(self):
    return self
    
  def __exit__(self, arg1, arg2, arg3):
    self.irqDetach()

  def __del__(self):
    self.irqDetach()
