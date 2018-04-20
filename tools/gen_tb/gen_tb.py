#!/usr/bin/env python3

import os, sys
import argparse

verbose=False
python_req_version = (3, 0, 1)
exec_name=os.path.realpath(sys.argv[0])

app_version = "0.6"
app_targets_dir = "/targets/"
app_src_dir = "/include/"
app_dir = os.path.dirname(exec_name)
app_prog = os.path.splitext(os.path.basename(exec_name))[0]

app_description = "Generates various types of testbenches for VHDL components according to description written\n\
in XML. Built testing sequences can be run in simulator or hardware environment."
app_epilog = app_prog + " version: " + app_version + "\nCopyright (C) 2015-2018 - Marcin 'obeny' Benka <obeny@obeny.net>\n\
This program may be freely redistributed under the terms of the GNU GPL v2"


#
# HELPER FUNCTIONS
# ================
def fatal(msg):
	print("FATAL: {0:s}; exitting...".format(msg))
	sys.exit(-1)

def checkPythonVersion():
	return sys.version_info >= python_req_version

def listTargets():
	targets_dir = app_dir + app_targets_dir;
	target_modules = os.listdir(targets_dir)
	targets = []
	for target in target_modules:
		if os.path.isfile(targets_dir + target):
			targets.append(os.path.splitext(target)[0])
	return targets

#
# RUN
# ===
def run():
	global verbose
	arg_parser = argparse.ArgumentParser(description=app_description, epilog=app_epilog,\
		prog=app_prog, formatter_class=argparse.RawDescriptionHelpFormatter)
	
	arg_parser.add_argument("xml", help="XML definition of testbenches")

	arg_parser.add_argument("--target", help="produces output for selected target", required=True, choices=listTargets())
	arg_parser.add_argument("--out", help="testbench output file", required=True)
	arg_parser.add_argument("--scripts", help="scripts directory", required=False)

	arg_parser.add_argument("--verbose", help="more verbose logging", action="store_true")
	arg_parser.add_argument("--version", action="version", version="%(prog)s-" + app_version)

	args = arg_parser.parse_args()

	xml = args.xml
	out = args.out
	scripts = args.scripts
	target_module = args.target
	verbose = args.verbose

	if os.path.splitext(xml)[1] != ".xml":
		fatal("File {0:s} is not XML".format(xml))
	if not os.path.isfile(xml):
		fatal("File {0:s} doesn't exist".format(xml))

	sys.path.append(os.path.abspath(app_dir + app_src_dir))
	sys.path.append(os.path.abspath(app_dir + app_targets_dir))
	sys.path.append(os.path.abspath(scripts))
	impl = __import__("impl")

	app = impl.AppGenTb(xml, out, scripts, target_module, verbose)
	app.run()

# ENTRY POINT
# ===========
if __name__ == "__main__":
	if checkPythonVersion():
		run()
	else:
		fatal("This program requires to be run with Python={0:d}.{1:d}.{2:d} or newer"\
			.format(python_req_version[0], python_req_version[1], python_req_version[2]))
		sys.exit(-1)
