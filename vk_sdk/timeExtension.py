"""Various extentions for time managing time"""

import time
from datetime import datetime

import pytz


class Timestamp(object):

    __slots__ = ('timestamp', 'diff', 'sync_tz')

    def __init__(self, timestamp=None, sync_tz="Europe/Moscow"):
        """
        :param timestamp=None: Used to Set the timestamp to the current time if it is not specified.
        :param sync_tz="Europe/Moscow": Used to Set the timezone to sync timestamp with.
        """
        self.sync_tz = sync_tz
        if timestamp is None:
            timestamp = time.time()
        self.timestamp = timestamp
        zrh = pytz.timezone(self.sync_tz)
        tztime = zrh.localize(datetime.fromtimestamp(self.timestamp))
        tzfloat = (tztime - datetime(1970, 1, 1,
                   tzinfo=pytz.utc)).total_seconds()
        self.diff = self.timestamp - tzfloat

    def get_time(self):
        return self.timestamp + self.diff

    def __float__(self):
        return self.get_time()

    def passed(self):
        return time.time() >= self.get_time()

    @classmethod
    def now(cls):
        """Create Timestamp class from current time"""
        return cls(time.time())

    def prettyprint(self):
        """
        The prettyprint function prints the contents of a object in a human-readable format.
           It is intended to be used for debugging purposes.
        
        :param self: Used to Reference the object to which the function is attached.
        :return: A string representation of the object.
        """
        return datetime.fromtimestamp(self.get_time()).strftime("%Y/%m/%d %H:%M:%S")
