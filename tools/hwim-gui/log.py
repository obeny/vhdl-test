import sys

from enum import IntEnum

class Verbosity(IntEnum):
	INFO = 0
	NOTE = 1
	DEBUG = 2
	ALL = 0xFF

class TermColor:
	RED = '\033[91m'
	ORANGE = '\033[33m'
	YELLOW = '\033[93m'
	GREEN = '\033[32m'
	LGREEN = '\033[92m'
	BLUE = '\033[94m'
	NC = '\033[0m'

verbose = Verbosity.ALL

def setVerbose(value):
	global verbose
	verbose = value


def fatal(msg):
	print(TermColor.RED +         "FATAL: " + TermColor.NC + msg + "; exitting...")
	sys.exit(-1)

def error(msg):
	print(TermColor.ORANGE +      "ERROR: " + TermColor.NC + msg +"; exitting...")
	sys.exit(-2)

def warning(msg):
	print(TermColor.YELLOW +      "WARN:  " + TermColor.NC + msg)

def info(msg):
	print(TermColor.GREEN +       "INFO:  " + TermColor.NC + msg)

def note(msg):
	if verbose >= Verbosity.NOTE:
		print(TermColor.BLUE +    "NOTE:  " + TermColor.NC + msg)

def debug(msg):
	if verbose >= Verbosity.DEBUG:
		print ("DEBUG: " + msg)
