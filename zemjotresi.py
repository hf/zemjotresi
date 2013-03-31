from lib import config
from lib import functions
from lib import timezones
from lib import feedparser
from lib import seismograph
from models import earthquake
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api import memcache
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

import os, re, logging, datetime

template.register_template_library('lib.templatefilters')

class ShutdownPage(webapp.RequestHandler):
  def get(self):
    template_values = {
      'host_url': self.request.host_url,
      'deployed': functions.deployed(self.request.host_url)
    }

    template_path = os.path.join(os.path.dirname(__file__), "template/base_shutdown.html")
    self.response.out.write(template.render(template_path, template_values))

class RedirectToShutdownPage(webapp.RequestHandler):
  def get(self):
    self.redirect("/")

class MainPage(webapp.RequestHandler):
  def get(self):
    today = datetime.datetime.utcnow().replace(tzinfo=timezones.UTC()).astimezone(timezones.UTC1()).replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - datetime.timedelta(1)

    entries_today = earthquake.Earthquake.gql("WHERE time >= :1 AND object_type = :2 ORDER BY time DESC", today, db.Category("Normal"))

    entries_yesterday = earthquake.get_yesterday(limit=5, order="ORDER BY time DESC")

    entries_before = earthquake.get_before(limit = 5)

    entries_special = earthquake.get_special()

    if re.search('highlight_today', self.request.query_string):
      highlight_today = True
    else:
      highlight_today = False

    template_values = {
      'entries_today': entries_today,
      'entries_yesterday': entries_yesterday,
      'entries_before': entries_before,
      'entries_special': entries_special,
      'entries_special_count': earthquake.get_special_count(),
      'entries_today_count': functions.count(entries_today),
      'entries_yesterday_count': earthquake.get_yesterday_count(),
      'today': today,
      'yesterday': yesterday,
      'now': datetime.datetime.utcnow().replace(tzinfo=timezones.UTC()),
      'highlight_today': highlight_today,
      'host_url': self.request.host_url,
      'deployed': functions.deployed(self.request.host_url)
    }

    template_path = os.path.join(os.path.dirname(__file__), "template/base_index.html")
    self.response.out.write(template.render(template_path, template_values))

class EarthquakeManager(webapp.RequestHandler):
  def get(self):
    k = self.request.path.split("/")[2]
    try:
      earthquake = db.get(k)

      if earthquake is None:
        self.redirect(self.request.host)

      today = datetime.datetime.utcnow().replace(tzinfo=timezones.UTC()).astimezone(timezones.UTC1()).replace(hour=0, minute=0, second=0, microsecond=0)
      yesterday = today - datetime.timedelta(1)

      earthquake_time = earthquake.time.replace(tzinfo=timezones.UTC()).astimezone(timezones.UTC1())

      if earthquake_time >= today:
        time_class = "today"
      elif earthquake_time >= yesterday and earthquake_time < today:
        time_class = "yesterday"
      else:
        time_class = "before"

      if earthquake.object_type == db.Category("Special"):
        time_class = "special"

      maps_api = config.Config().google_maps_api_key()

      template_values = {
        'earthquake': earthquake,
        'time_class': time_class,
        'today': today,
        'yesterday': yesterday,
        'maps_api': maps_api,
        'host_url': self.request.host_url,
        'deployed': functions.deployed(self.request.host_url)
      }

      template_path = os.path.join(os.path.dirname(__file__), "template/base_earthquake.html")
      self.response.out.write(template.render(template_path, template_values))
    # if some error happens, just redirect
    except:
      self.redirect('/')

class TimeManager(webapp.RequestHandler):
  def get(self):
    t = self.request.path.split('/')[1]
    q = self.request.query_string

    page = 0
    per_page = 10

    # this piece of code fishes out query strings, and even though it may appear
    # quite scary and confusing, it actually has never been fishing before
    # not for query strings, not even for fishes
    if q:
      if q.find("&") > -1:
        q = q.split("&")
        for i in range(0, len(q)):
          if q[i].find("=") > -1:
            q[i] = q[i].split("=")
            if q[i][0] == 'page' or q[i][0] == 'strana':
              page = int(q[i][1])
            elif q[i][0] == 'per_page' or q[i][0] == 'po_strana':
              per_page = int(q[i][1])
      elif q.find("&") < 0 and q.find("=") > -1:
        q = q.split("=")
        if q[0] == 'page' or q[0] == 'strana':
          page = int(q[1])
        elif q[0] == 'per_page' or q[0] == 'po_strana':
          per_page = int(q[1])

    today = datetime.datetime.utcnow().replace(tzinfo=timezones.UTC()).astimezone(timezones.UTC1()).replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - datetime.timedelta(1)

    time_class = ''

    if t == 'vcera' or t == 'vchera':
      entries_count = earthquake.get_yesterday_count()

      if entries_count > 0:
        entries = earthquake.get_yesterday(
          limit= "%s OFFSET %s" % (per_page, page*per_page),
          order= "ORDER BY time DESC"
        )
      else:
        entries = []

      time_class = 'yesterday'
      time_class_cyr = '\xd0\x92\xd1\x87\xd0\xb5\xd1\x80\xd0\xb0'

    elif t == 'predtoa':
      entries_count = earthquake.get_before_count()

      if entries_count > 0:
        entries = earthquake.get_before(
          limit= "%s OFFSET %s" % (per_page, page*per_page),
          order= "ORDER BY time DESC"
        )
      else:
        entries = []

      time_class = 'before'
      time_class_cyr = '\xd0\x9f\xd1\x80\xd0\xb5\xd0\xb4\xd1\x82\xd0\xbe\xd0\xb0'
    # TODO: add a 'thedayaftertomorrow' timeline option :P


    # some pagination magic!
    if per_page > entries_count:
      per_page = entries_count

    if per_page == 0:
      max_pages = 1
    else:
      max_pages = (entries_count / per_page) - 1

    # if a person lands on an empty airfield,
    # tell his plane to re-land on the other, closest to this one
    # and please, oh please do tell
    # that the person cannot land!
    if page > max_pages:
      self.redirect(self.request.host_url +
        self.request.path +
        "?page=" + str(max_pages) +
        "&per_page=" + str(per_page))


    if page + 1 <= max_pages:
      next_page = page + 1
    else:
      next_page = None

    if page - 1 > -1:
      prev_page = page - 1
    else:
      prev_page = None


    if time_class == 'yesterday':
      simpletime = 1
    else:
      simpletime = None

    template_values = {
      'entries': entries,
      'entries_count': entries_count,
      'time_class': time_class,
      'time_class_cyr': time_class_cyr,
      'next_page': next_page,
      'prev_page': prev_page,
      'per_page': per_page,
      'simpletime': simpletime,
      'yesterday': yesterday,
      'host_url': self.request.host_url,
      'deployed': functions.deployed(self.request.host_url)
    }

    template_path = os.path.join(os.path.dirname(__file__), "template/base_timeline.html")
    self.response.out.write(template.render(template_path, template_values))


class FeedManager(webapp.RequestHandler):
  def get(self):
    last_change = earthquake.Earthquake.gql("ORDER BY time DESC LIMIT 1")
    for chng in last_change:
      last_change = chng
      break

    entries = earthquake.Earthquake.gql("ORDER BY time DESC LIMIT 15")

    template_values = {
      'entries': entries,
      'uri': self.request.uri,
      'last_change': last_change,
      'host_url': self.request.host_url
    }

    template_path = os.path.join(os.path.dirname(__file__), "template/feed/atom.xml")
    self.response.headers['Content-Type'] = 'application/atom+xml'
    self.response.out.write(template.render(template_path, template_values))

class CronUpdate(webapp.RequestHandler):
  def get(self):
    s = seismograph.Seismograph()
    sense_data = s.sense()
    s.add_to_db(sense_data)

class MemcacheStats(webapp.RequestHandler):
  def get(self):
    self.response.out.write(memcache.get_stats())

class MemcacheFlush(webapp.RequestHandler):
  def get(self):
    memcache.flush_all()
    self.redirect('/')

class DeleteEverything(webapp.RequestHandler):
  def get(self):
    everything = db.GqlQuery("SELECT __key__ FROM Earthquake ORDER BY time DESC")
    everything = everything.fetch(1000)
    self.response.out.write("Please wait. Deleting everything!")

    db.delete(everything)


application = webapp.WSGIApplication([('/', MainPage),
                                      #('/atom', FeedManager),
                                      ('/update', CronUpdate),
                                      #(r'/predtoa', TimeManager),
                                      ('/memcache_stats', MemcacheStats),
                                      ('/memcache_flush', MemcacheFlush),
                                      ('/delete_everything', DeleteEverything),
                                      #(r'/.*', RedirectToShutdownPage), # since shutdown
                                      (r'/zemjotres/.*', EarthquakeManager),
                                      (r'/.*', TimeManager)
                                     ],
                                     debug=True)
if __name__ == "__main__":
  logging.getLogger().setLevel(logging.DEBUG)
  run_wsgi_app(application)

