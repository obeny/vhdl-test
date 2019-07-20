import sys

verbose = False

def setVerbose(value):
	global verbose
	verbose = value

def error(msg):
	print("ERROR: {0:s}; exitting...".format(msg))
	sys.exit(-2)

def fatal(msg):
	print("FATAL: " + msg)

def info(msg):
	if verbose:
		print("INFO:  " + msg)

def note(msg):
	if verbose:
		print("NOTE:  " + msg)
