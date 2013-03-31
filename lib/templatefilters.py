import datetime
from lib import timezones
from google.appengine.ext.webapp import template
from google.appengine.ext import db

def rnd(number):
  return int(round(number))

def format_rfc3339(dt):
  if dt.tzinfo is not None:
    return str(dt).replace(' ', 'T')
  else:
    return str(dt).replace(' ', 'T') + 'Z'

def format_date_macedonian(dt):
  return dt.strftime("%d.%m.20%y")

def format_datetime_macedonian(dt):
  return dt.strftime("%d.%m.20%y %H:%M:%S")

def format_time_macedonian(t):
  return t.strftime("%H:%M:%S")

def time_utc1(dt):
  return dt.replace(tzinfo=timezones.UTC()).astimezone(timezones.UTC1()).time()

def time_hour_utc1(dt):
  return dt.astimezone(timezones.UTC1()).hour

def time_minutes_utc1(dt):
  return dt.astimezone(timezones.UTC1()).minute

def datetime_utc1(dt):
  return dt.replace(tzinfo=timezones.UTC()).astimezone(timezones.UTC1())

def not_none(var):
  if var != None:
    return True
  else:
    return False
    
def is_warning(magnitude):
  if magnitude >= 4.3:
    return True
  else:
    return False
    
def split(t):
  if len(t) > 0:
    return t.split("\n")
  else:
    return None

def is_special(klass):
  klass = klass.lower()
  if klass == "special":
    return True
  else:
    return False

register = template.create_template_register()
register.filter(format_rfc3339)
register.filter(format_date_macedonian)
register.filter(format_time_macedonian)
register.filter(format_datetime_macedonian)
register.filter(time_utc1)
register.filter(time_hour_utc1)
register.filter(time_minutes_utc1)
register.filter(datetime_utc1)
register.filter(rnd)
register.filter(not_none)
register.filter(is_warning)
register.filter(split)
register.filter(is_special)

