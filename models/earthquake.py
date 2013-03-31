from google.appengine.ext import db
from google.appengine.api import memcache
from lib import timezones
import hashlib
import datetime

class Earthquake(db.Model):
  location = db.StringProperty()
  position = db.GeoPtProperty()
  time = db.DateTimeProperty()
  magnitude = db.FloatProperty()
  magnitude_type = db.CategoryProperty() # Short form, eg. Richter => ML
  depth = db.FloatProperty()
  object_type = db.CategoryProperty() # Normal or Special
  extra = db.TextProperty() # Usually used when "object_type" is "Special"
  details = db.LinkProperty()

  created_at = db.DateTimeProperty(auto_now_add=True)

def generate_memcache_key(about, binder=None, klass=None):
  now = datetime.datetime.utcnow().replace(tzinfo=timezones.UTC()) \
                                  .astimezone(timezones.UTC1())

  today = now.date()
  yesterday = today - datetime.timedelta(1)

  md5 = hashlib.md5()

  if binder is not None:
    identifier = "%s::%s" % (str(today), str(binder).lower())
  else:
    identifier = str(today)

  if about == "before" or about == "yesterday" or about == "special":
    md5.update(identifier)
    if klass is not None:
      return "%s_%s_%s" % (about, md5.hexdigest(), klass)
    else:
      return "%s_%s" % (about, md5.hexdigest())
  else:
    return None

def generate_expiration_time():
  now = datetime.datetime.utcnow().replace(tzinfo=timezones.UTC()) \
                                  .astimezone(timezones.UTC1())
  tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + \
                datetime.timedelta(1)

  return (tomorrow - now).seconds
  
def get_special_count():
  now = datetime.datetime.utcnow().replace(tzinfo=timezones.UTC()) \
                                  .astimezone(timezones.UTC1())

  today = now.replace(hour=0, minute=0, second=0, microsecond=0)
  yesterday = today - datetime.timedelta(1)

  memcache_key = generate_memcache_key("special", klass="count")
  count = memcache.get(memcache_key)
  if count is not None:
    return count
  else:
    data = Earthquake.gql("WHERE object_type = :1", db.Category("Special"))
    count = 0
    
    for d in data:
      t = d.time
      if t.day == today.day and t.month == today.month:
        count += 1
        
    memcache.add(memcache_key, count, generate_expiration_time())
    return count
    
def get_special(limit=None, query=None, order=None):
  now = datetime.datetime.utcnow().replace(tzinfo=timezones.UTC()) \
                                  .astimezone(timezones.UTC1())

  today = now.replace(hour=0, minute=0, second=0, microsecond=0)
  yesterday = today - datetime.timedelta(1)

  # Due to Python's bad handling of None and str() one must waste keystrokes
  # on procedures like these:
  if limit is None:
    limit = ''
  else:
    limit = "LIMIT %s" % str(limit)
  if query is None:
    query = ''
  if order is None:
    order = 'ORDER BY time DESC'

  identifier = "%s.%s.%s" % (query, order, limit)
  memcache_key = generate_memcache_key("special", binder=identifier)

  data_special = memcache.get(memcache_key)
  if data_special is not None:
    return data_special
  else:
    compiled_query = " %s %s %s" % (query, order, limit)
    data_special = Earthquake.gql("WHERE object_type = :1" + compiled_query, db.Category("Special"))
    
    specials = []
    
    for special in data_special:
      t = special.time.replace(tzinfo=timezones.UTC()).astimezone(timezones.UTC1())
      if t.day == today.day+1 and t.month == today.month:
        specials.append(special)
      
    memcache.add(memcache_key, specials, generate_expiration_time())
    return specials


def get_yesterday_count():
  now = datetime.datetime.utcnow().replace(tzinfo=timezones.UTC()) \
                                  .astimezone(timezones.UTC1())

  today = now.replace(hour=0, minute=0, second=0, microsecond=0)
  yesterday = today - datetime.timedelta(1)

  memcache_key = generate_memcache_key("yesterday", klass="count")
  count = memcache.get(memcache_key)
  if count is not None:
    return count
  else:
    data = Earthquake.gql("WHERE object_type = :1 AND time >= :2 AND time < :3", db.Category("Normal"), yesterday, today)
    data_count = data.count()
    memcache.add(memcache_key, data_count, generate_expiration_time())
    return data_count

def get_yesterday(limit=None, query=None, order=None):
  # "query" should not contain the GQL keywords "WHERE", "ORDER" and "LIMIT"
  # If "limit" has been set, then the query should not contain the GQL "LIMIT"
  # keyword. It can, however be a string and contain the GQL "OFFSET" keyword.
  # For eg. limit = 5, limit = "5 OFFSET 1", but *NOT* limit = "LIMIT 5 OFFSET 1"
  # If "order" isn't set, the results will be ordered in a descending direction
  # based on time. "order" should be a properly formatted GQL string, for eg.
  # "ORDER BY <property> <direction>, <property> <direction> ..."

  now = datetime.datetime.utcnow().replace(tzinfo=timezones.UTC()) \
                                  .astimezone(timezones.UTC1())

  today = now.replace(hour=0, minute=0, second=0, microsecond=0)
  yesterday = today - datetime.timedelta(1)

  # Due to Python's bad handling of None and str() one must waste keystrokes
  # on procedures like these:
  if limit is None:
    limit = ''
  else:
    limit = "LIMIT %s" % str(limit)
  if query is None:
    query = ''
  if order is None:
    order = 'ORDER BY time DESC'

  identifier = "%s.%s.%s" % (query, order, limit)
  memcache_key = generate_memcache_key("yesterday", binder=identifier)

  data_yesterday = memcache.get(memcache_key)
  if data_yesterday is not None:
    return data_yesterday
  else:
    compiled_query = " %s %s %s" % (query, order, limit)
    data_yesterday = Earthquake.gql("WHERE time >= :1 AND time < :2 AND object_type = :3" + compiled_query, yesterday, today, db.Category("Normal"))
    memcache.add(memcache_key, data_yesterday, generate_expiration_time())
    return data_yesterday


def get_before_count():
  now = datetime.datetime.utcnow().replace(tzinfo=timezones.UTC()) \
                                  .astimezone(timezones.UTC1())

  today = now.replace(hour=0, minute=0, second=0, microsecond=0)
  yesterday = today - datetime.timedelta(1)

  memcache_key = generate_memcache_key("before", klass="count")
  count = memcache.get(memcache_key)
  if count is not None:
    return count
  else:
    data = Earthquake.gql("WHERE time < :1 AND object_type = :2", yesterday, db.Category("Normal"))
    data_count = data.count()
    memcache.add(memcache_key, data_count, generate_expiration_time())
    return data_count

def get_before(limit=None, query=None, order=None):
  # "query" should not contain the GQL keywords "WHERE", "ORDER" and "LIMIT"
  # If limit has been set, then the query should not contain the GQL "LIMIT"
  # keyword. It can, however be a string and contain the GQL "OFFSET" keyword.
  # For eg. limit = 5, limit = "5 OFFSET 1", but *NOT* limit = "LIMIT 5 OFFSET 1"
  # If order isn't set, the results will be ordered in a descending direction
  # based on time. "order" should be a properly formatted GQL string, for eg.
  # "ORDER BY <property> <direction>, <property> <direction> ..."

  now = datetime.datetime.utcnow().replace(tzinfo=timezones.UTC()) \
                                  .astimezone(timezones.UTC1())

  today = now.replace(hour=0, minute=0, second=0, microsecond=0)
  yesterday = today - datetime.timedelta(1)

  # Due to Python's bad handling of None and str() one must waste keystrokes
  # on procedures like these:
  if limit is None:
    limit = ''
  else:
    limit = "LIMIT %s" % str(limit)
  if query is None:
    query = ''
  if order is None:
    order = 'ORDER BY time DESC'

  identifier = "%s.%s.%s" % (query, order, limit)
  memcache_key = generate_memcache_key("before", binder=identifier)

  data_before = memcache.get(memcache_key)
  if data_before is not None:
    return data_before
  else:
    compiled_query = " %s %s %s" % (query, order, limit)
    data_before = Earthquake.gql("WHERE time < :1 AND object_type = :2" + compiled_query, yesterday, db.Category("Normal"))
    memcache.add(memcache_key, data_before, generate_expiration_time())
    return data_before

