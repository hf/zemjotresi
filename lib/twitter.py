from django.utils import simplejson as json
from google.appengine.api import urlfetch
import base64
import urllib
import re

class Twitter():
  def __init__(self, username, password):
    self.username = username
    self.password = password
    self.credentials = "%s:%s" % (username, password)
    self.credentials = base64.b64encode(self.credentials)
    self.update_url = u"http://twitter.com/statuses/update.json"

  # uses 0.mk!      
  def shorten_url(self, long_url):
    url = "http://api.0.mk/?dolg=%s" % urllib.quote(long_url)
    data = urlfetch.fetch(url).content
    
    if re.match("http://.*", data) is not None:
      return data
    else:
      return False

  def update_status(self, status):
    url = self.update_url + "?status=%s" % urllib.quote(status)
    h = {'Authorization': 'Basic ' + self.credentials}
    data = urlfetch.fetch(url, method=urlfetch.POST, headers=h)

    if data.status_code == 200:
      data = json.loads(data.content)
      return {'good': True, 'id': data["id"]}
    elif data.status_code == 403:
      data = json.loads(data.content)
      return {'good': False, 'error': 403, 'message': data["error"]}
    else:
      return {'good': False, 'error': data.statsus_code, 'data': json.loads(data.content)}

