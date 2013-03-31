from google.appengine.ext import db
from google.appengine.tools import bulkloader
import datetime

# model
class Earthquake(db.Model):
  location = db.StringProperty()
  position = db.GeoPtProperty()
  time = db.DateTimeProperty()
  magnitude = db.FloatProperty()
  magnitude_type = db.CategoryProperty() # Short form, eg. Richter => ML; UKN when there is a lack of data
  depth = db.FloatProperty()
  object_type = db.CategoryProperty() # Normal or Special
  extra = db.TextProperty() # Usually used when "kind" is "Special"
  details = db.LinkProperty()

  created_at = db.DateTimeProperty(auto_now_add=True)

def serialize_extra(ex):
  ex = unicode(ex, 'utf-8')
  if ex.find("None") != 0:
    return db.Text(ex)
  else:
    return db.Text("")

class EarthquakeLoader(bulkloader.Loader):
  def __init__(self):
    bulkloader.Loader.__init__(self, 'Earthquake',
                                  [('location', lambda x: unicode(x, 'utf-8')),
                                   ('position', lambda x: db.GeoPt(float(x.split()[0]), lon=float(x.split()[1]))),
                                   ('time', lambda x: datetime.datetime.strptime(x, "%Y-%m-%d %H:%M:%S")),
                                   ('magnitude', float),
                                   ('magnitude_type', lambda x: db.Category(x)),
                                   ('depth', float),
                                   ('details', lambda x: db.Link(x)),
                                   ('created_at', lambda x: datetime.datetime.strptime(x, "%Y-%m-%d %H:%M:%S.%f")),
                                   ('object_type', lambda x: db.Category(x)),
                                   ('extra', serialize_extra),
                               ])

loaders = [EarthquakeLoader]
