import re

import log

# TimeUtils static class - simplifies operations on time
class TimeUtils:
	@staticmethod
	def timeToInterval(time):
		ret = ""
		prefix = ""
		value = TimeUtils.getTimeValue(time)

		if value >= 1000:
			log.error("timeToInterval: couldn't convert time={0:d} to interval, given value too big (>=1000)"\
				.format(value))

		unit = TimeUtils.getTimeUnit(time)
		if unit == 'ns':
			prefix = 'n'
		elif unit == 'us':
			prefix = 'u'
		elif unit == 'ms':
			prefix = 'm'
		elif unit == 's':
			prefix = 's'
		else:
			log.error("timeToInterval: invalid time unit={0:s}".format(unit))

		ret += prefix
		ret += "{0:03d}".format(value)
		return ret

	@staticmethod
	def intervalToTime(interval):
		ret = ""
		unit = ""

		interval_value = int(re.sub(r"^0+", "", interval[1:4]))
		if inverval[0] == 'n':
			unit = 'ns'
		elif interval[0] == 'u':
			unit = 'us'
		elif interval[0] == 'm':
			unit = 'ms'
		elif interval[0] == 's':
			unit = 's'
		else:
			log.error("intervalToTime: invalid interval definition: \'" + interval + "\'")

		return (str(interval_value) + " " + unit)

	@staticmethod
	def getTimeValue(time):
		return int(time.split(" ")[0])

	@staticmethod
	def getTimeUnit(time):
		return time.split(" ")[1]

	@staticmethod
	def timeValueInNsFromInterval(interval):
		interval_value = int(re.sub(r"^0+", "", interval[1:4]))

		if interval[0] == 'u':
			interval_value *= 1000
		elif interval[0] == 'm':
			interval_value *= 1000000
		elif interval[0] == 's':
			interval_value *= 1000000000
		elif interval[0] != 'n':
			log.error("timeValueInNsFromInterval: invalid interval definition: \'" + interval + "\'")

		return interval_value

	@staticmethod
	def timeValueInNsFromTime(time):
		value = TimeUtils.getTimeValue(time)
		unit = TimeUtils.getTimeUnit(time)

		if unit == 'us':
			value *= 1000
		elif unit == 'ms':
			value *= 1000000
		elif unit == 's':
			value *= 1000000000
		elif unit != 'ns':
			log.error("timeValueInNsFromTime: invalid time definition: \'" + time + "\'")

		return value
