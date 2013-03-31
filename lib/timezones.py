from datetime import timedelta, datetime, tzinfo

class UTC1(tzinfo):
  def utcoffset(self, dt):
    return timedelta(hours=1) + self.dst(dt)

  def dst(self, dt):
    dst_start = datetime(dt.year, 4, 1) - timedelta(days=datetime(dt.year, 4, 1).weekday() + 1)
    dst_end = datetime(dt.year, 11, 1) - timedelta(days=datetime(dt.year, 4, 1).weekday() + 1)
    if dst_start <= dt.replace(tzinfo=None) < dst_end:
      return timedelta(hours=1)
    else:
      return timedelta(0)

  def tzname(self, dt):
    return "UTC +1"

class UTC(tzinfo):
  def utcoffset(self, dt):
    return timedelta(0)

  def dst(self, dt):
    return timedelta(0)

  def tzname(self, dt):
    return "UTC"

