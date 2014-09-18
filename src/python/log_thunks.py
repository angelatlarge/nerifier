class FakeLogger:
  @classmethod
  def debug(cls, msg): print msg
  @classmethod
  def info(cls, msg): print msg
  @classmethod
  def error(cls, msg): print msg

class NoLogger:
  @classmethod
  def debug(cls, msg): pass
  @classmethod
  def info(cls, msg): pass
  @classmethod
  def error(cls, msg): pass
