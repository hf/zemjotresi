import re
import datetime
from lib import config, timezones
from google.appengine.api import urlfetch
from django.utils import simplejson as json

# -*- coding: utf-8 -*-

def deployed(host_url):
  if re.search("localhost", host_url) or re.search("127.0.0.1", host_url):
    return False
  else:
    return True

def count(query, filter_magnitude_type=True):
  c = 0
  if filter_magnitude_type:
    for q in query:
      if q.magnitude_type != 'UKN':
        c += 1
  else:
    for q in query:
      c += 1

  return c

def is_cyrillic(string):
  vowels = [u'\u0430', u'\u0435', u'\u0438', u'\u043e', u'\u0443', u'\u0440']
  string = string.lower()
  passed = False

  for vowel in vowels:
    if string.find(vowel) != -1:
      passed = True

  return passed

def to_cyrillic(city_name):
  cities = {
    u"Valandovo": u'\u0412\u0430\u043b\u0430\u043d\u0434\u043e\u0432\u043e',
    u"Strumica": u'\u0421\u0442\u0440\u0443\u043c\u0438\u0446\u0430',
    u"Novo Selo": u'\u041d\u043e\u0432\u043e \u0441\u0435\u043b\u043e',
    u"Bitola": u'\u0411\u0438\u0442\u043e\u043b\u0430',
    u"\u0160tip": u'\u0428\u0442\u0438\u043f',
    u"Sveti Nikole": u'\u0421\u0432\u0435\u0442\u0438 \u041d\u0438\u043a\u043e\u043b\u0435'
  }

  to_return = u''

  if not is_cyrillic(city_name):
    try:
      to_return = cities[city_name]
    except KeyError:
      return city_name
  else:
    return city_name

  return to_return

def string_to_datetime(string):
  time = string.split(u'\xa0\xa0')
  time = time[0] + ' '.encode('utf8') + time[1]
  time = time.split('.'.encode('utf8'))
  milliseconds = time[1]
  time.pop(1)

  dt = datetime.datetime.strptime(time[0], "%Y-%m-%d %H:%M:%S") + datetime.timedelta(milliseconds=int(milliseconds)*1000)

  dt.replace(tzinfo=timezones.UTC())

  return dt


def geocode_location(latitude, longitude):
  cnf = config.Config()
  key = cnf.google_maps_api_key()
  url = "http://maps.google.com/maps/geo?" + "q=" + str(latitude) + "," + str(longitude) + "&sensor=false" + "&output=json" + "&oe=utf8" + "&gl=mk" + "&key=" + key
  data = urlfetch.fetch(url)
  try:
    if data.status_code == 200:
      data = json.loads(data.content)
      location = ''

      for place in data['Placemark']:
        if re.search("Macedonia", place['AddressDetails']['Country']['CountryName']) and (place['AddressDetails']['Accuracy'] == 4 or place['AddressDetails']['Accuracy'] == 5):
          # TODO: Transcribe from latin into cyrillic
          location = place['AddressDetails']['Country']['Locality']['LocalityName']
          break
  except:
    return ''



def generate_google_maps_link(latitude, longitude, zoom=25, view_type='h'):
  url = "http://maps.google.com/?ie=UTF8&ll=" + str(latitude) + ',' + str(longitude) + "&z=" + str(zoom) + "&t=" + view_type

  return url

