#!/usr/bin/env python

import os, sys
import oe, oe.data

def getfields(line):
	fields = {}
	fieldmap = ( "pkg", "src", "dest", "type", "mode", "uid", "gid", "major", "minor", "start", "inc", "count" )
	for f in xrange(len(fieldmap)):
		fields[fieldmap[f]] = None

	if not line:
		return None

	splitline = line.split()
	if not len(splitline):
		return None

	try:
		for f in xrange(len(fieldmap)):
			if splitline[f] == '-':
				continue
			fields[fieldmap[f]] = splitline[f]
	except IndexError:
		pass
	return fields

def parse (mfile, d):
	manifest = []
	while 1:
		line = mfile.readline()
		if not line:
			break
		if line.startswith("#"):
			continue
		fields = getfields(line)
		if not fields:
			continue
		manifest.append(fields)
	return manifest

def emit (func, manifest, d):
#str = "%s () {\n" % func
	str = ""
	for line in manifest:
		emittedline = emit_line(func, line, d)
		if not emittedline:
			continue
		str += emittedline + "\n"
#	str += "}\n"
	return str

def mangle (func, line, d):
	import copy
	newline = copy.copy(line)
	src = oe.data.expand(newline["src"], d)

	if src:
		if not os.path.isabs(src):
			src = "${WORKDIR}/" + src

	dest = newline["dest"]
	if not dest:
		return

	if dest.startswith("/"):
		dest = dest[1:]

	if func is "do_install":
		dest = "${D}/" + dest

	elif func is "do_populate":
		dest = "${WORKDIR}/install/" + newline["pkg"] + "/" + dest

	elif func is "do_stage":
		varmap = {}
		varmap["${bindir}"] = "${STAGING_DIR}/${HOST_SYS}/bin"
		varmap["${libdir}"] = "${STAGING_DIR}/${HOST_SYS}/lib"
		varmap["${includedir}"] = "${STAGING_DIR}/${HOST_SYS}/include"
		varmap["${datadir}"] = "${STAGING_DATADIR}"

		matched = 0
		for key in varmap.keys():
			if dest.startswith(key):
				dest = varmap[key] + "/" + dest[len(key):]
				matched = 1
		if not matched:
			newline = None
			return
	else:
		newline = None
		return

	newline["src"] = src
	newline["dest"] = dest
	return newline

def emit_line (func, line, d):
	import copy
	newline = copy.deepcopy(line)
	newline = mangle(func, newline, d)
	if not newline:
		return None

	str = ""
	type = newline["type"]
	mode = newline["mode"]
	src = newline["src"]
	dest = newline["dest"]
	if type is "d":
		str = "install -d "
		if mode:
			str += "-m %s " % mode
		str += dest
	elif type is "f":
		if not src:
			return None
		if dest.endswith("/"):
			str = "install -d "
			str += dest + "\n"
			str += "install "
		else:
			str = "install -D "
		if mode:
			str += "-m %s " % mode
		str += src + " " + dest
	del newline
	return str
