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

class EarthquakeExporter(bulkloader.Exporter):
  def __init__(self):
    bulkloader.Exporter.__init__(self, 'Earthquake',
                                  [('location', lambda x: x.encode('utf-8'), None),
                                   ('position', lambda x: str(x.lat) + " " + str(x.lon), None),
                                   ('time', str, None),
                                   ('magnitude', float, None),
                                   ('magnitude_type', str, None),
                                   ('depth', float, None),
                                   ('details', str, None),
                                   ('created_at', str, None),
                                   ('object_type', str, None),
                                   ('extra', lambda x: x.encode('utf-8'), None),
                               ])

exporters = [EarthquakeExporter]
