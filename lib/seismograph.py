from lib import feedparser
from google.appengine.ext import db
from google.appengine.api import mail
import re
import datetime
import logging
import random
import os

from models import earthquake
from lib import functions, timezones, config
from lib.twitter import Twitter

from google.appengine.ext.webapp import template
from google.appengine.api import memcache

class Seismograph():
  def __init__(self, select_terms=None, update_interval=None):
    if select_terms:
      self.select_terms = select_terms
    else:
      self.select_terms = "FYR OF MACEDONIA"

  def sense(self):
    logging.debug("Sensing...")
    self.feed = feedparser.parse("http://www.emsc-csem.org/rss.php")
    self.entries = self.feed['entries']
    to_remove = []

    for i in range(0, len(self.entries)):
      if re.search("FYR OF MACEDONIA", self.entries[i]['title']) == None:
        to_remove.append(i)

    to_remove.sort()

    for i in reversed(to_remove):
      self.entries.pop(i)

    logging.debug("Removed " + str(len(to_remove)) + " entries.")

    return self.entries

  def insert_in_db(self, entry, dt):
    if len(entry['mag']) <= 2 and entry['mag'].split()[1] <= 0.1:
      logger.info("Cannot add entry into database. Too little information.")
      return False

    logging.debug("Inserting Earthquake in Database.")
    logging.debug(str(entry))

    eq = earthquake.Earthquake()
    eq.location = functions.geocode_location(float(entry['geo_lat']), float(entry['geo_long']))
    if eq.location is not '':
      logger.info("Possible correct reverse geocoding!")
      message = mail.MailMessage(subject="Zemjotresi: Possible correct reverse geocoding!",
                                 sender="Zemjotresi <sdimitrovski@gmail.com>",
                                 to="Stojan Dimitrovski <sdimitrovski@gmail.com>")
      message.body = """
Hello dear Creator,

I am hereby declaring that I might have again succeded in reverse geocoding a seismological event. You know, the thing you humans tend to call 'earthquakes.'

Now, I am compelled to ask a check from you; I can't be wrong that often, right? You are my Creator!

If I have done something wrong, please do tell (read: fix), if not cheer for my successful return for I shall rule the world again!

Goodbye,
Creator of Mine
"""

      message.send()

    eq.time = dt
    eq.magnitude = float(entry['mag'].split()[1])
    eq.magnitude_type = db.Category(entry['mag'].split()[0].upper())

    eq.position = db.GeoPt(float(entry['geo_lat']), float(entry['geo_long']))
    try:
      eq.depth = float(entry['depth'])
    except:
      eq.depth = 10.0

    eq.details = db.Link(entry['link'])
    eq.object_type = db.Category("Normal")
    eq.extra = db.Text("")
    eq.put()

    self.tweet_earthquake(str(eq.key()))

    return True

  def add_to_db(self, list_of_entries=None):
    if list_of_entries == None:
      list_of_entries = self.entries

    try:
      last = earthquake.Earthquake.gql("ORDER BY time DESC LIMIT 1")
      to_return = False
      for entry in list_of_entries:
        entry_date = functions.string_to_datetime(entry['updated'])

        if entry_date > last[0].time:
          self.insert_in_db(entry, dt=entry_date)
          to_return = True
    except IndexError:
      logging.info("Caught IndexError in add_to_db, most likely an initial update.")
      for entry in list_of_entries:
        self.insert_in_db(entry, dt=functions.string_to_datetime(entry['updated']))
        to_return = True

      if to_return is not False:
        memcache.flush_all()

    return to_return

  def tweet_earthquake(self, earthquake_key):
    # Always call this method after adding to the DB.
    earthquake = db.get(earthquake_key)
    if earthquake.magnitude <= 0.0 and len(earthquake.location) > 0:
      cnf = config.Config()
      t_creds = cnf.twitter_credentials()
      t = Twitter(t_creds['username'], t_creds['password'])
      bitly_creds = cnf.bitly_credentials()
      url = "http://zemjotresi.appspot.com/zemjotres/%s" % earthquake_key
      short_url = t.shorten_url(url)

      if short_url['good']:
        short_url = short_url['url']
      else:
        logging.error("Coulnd't shorten url (%s). Data: %s." % (url, short_url))
        return False

      template_id = int(round(random.uniform(1, 2)))
      template_path = os.path.join(os.path.dirname(__file__), "../template/tweets/tweet_%s.txt" % template_id)
      tweet = template.render(template_path, {'earthquake': earthquake, 'short_url': short_url})

      status = t.update_status(tweet)

      if status['good']:
        logging.info("Tweeted status_id: %s !" % status["id"])
      elif status['good'] == False and status["error"] == 403:
        logging.error("Couldn't tweet status for (%s). Exceeded update limit, got message: %s!" % (earthquake_key, status['message']))
      else:
        logging.error("Couldn't tweet status for (%s). Got error %s with data: %s!" % (earthquake_key, status['error'], status['data']))
    else:
      logging.info("Not tweeting status for (%s)!" % earthquake_key)

