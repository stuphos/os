#!/usr/local/bin/python
'Classes in this module read and write Zifnab\'s "Searches" from file.'
# Written by Fraun - Nov 9th 2005 (Modelled after the objlib reader)
#   Todo:  Decide on name of module: schlib? searchlib?
#          Invoke the --options from WSGI
#          Implement a lint detector for tildes and hash marks in front of strings (possibly stripping them)

from .dblib import RecordReader, FormatError, makePrintable
from os import getenv
from sys import stdout
from os.path import join, exists, basename
from pprint import pprint
from linecache import getline
from sys import exc_info


class SearchReader(RecordReader):
	# A little customization.
	MALFORMED_FIRST_RECORD_FMT='Malformed first search record header %c%r (expected #<Room Virtual NR>)'
	VirtualNRName = 'roomVNR'

	# This overloads the name of the vno in the record.
	# def newRecord(self, vnr):
	#	'Start of new current search record'
	#	# Merge searches for same rooms!  XXX This isn't supported yet!
	#	r = super(RecordReader, self).newRecord(vnr)
	#	s = self.getRecordSet()
	#	a = s.get(vnr, [])
	#	a.append(r)
	#	s[vnr] = a

	def parseRecord(self):
		'Load record area into logical Python object.  Returns the next Room VNR parsed.'

		# Pass each field read to handler function
		kind, reset = list(map(int, self.readLine().split()))
		self.recordField('type',     kind)
		self.recordField('reset',    reset)

		self.recordField('intval',   list(map(int,   self.readLine().split())))
		self.recordField('longval',  list(map(int,  self.readLine().split())))

		self.recordField('cmd',      self.tildeString('command'))
		self.recordField('noargs',   self.tildeString('command-sans-args'))
		self.recordField('keywords', self.tildeString('keywords'))

		self.recordField('strval',   list(map(lambda n, rs=self.tildeString:rs('string%d'%(n+1)), range(8))))
		self.recordField('objVNR',   int(self.readLine()))

		line=self.readLine()
		if line:
			c=line[0]
			if c=='$':        # detected end of records
				return    # return None-value to terminate caller

			if c=='#':        # start of next record
				return int(line[1:])

			raise FormatError("Trailing search record: '%s'" % makePrintable(c))

		# No $ at terminating records at end of file
		return self.EOFNoDollar()


##  The following code connects the reader with the filesystem given a CLI.
##  Also output routines that regenerate the .sch file format.

## Whitespace in this format is significant (notice beginning and end of string)
SEARCH_RECORD_FMT=\
"""#%(roomVNR)d
%(type)d %(reset)d
%(ival0)d %(ival1)d %(ival2)d %(ival3)d %(ival4)d %(ival5)d
%(lval0)ld %(lval1)ld
%(cmd)s~
%(noargs)s~
%(keywords)s~
%(sval0)s~
%(sval1)s~
%(sval2)s~
%(sval3)s~
%(sval4)s~
%(sval5)s~
%(sval6)s~
%(sval7)s~
%(objVNR)d"""

def formatSearches(out, sch, fmt=SEARCH_RECORD_FMT):
	'''
	This routine takes a file-like object for printing, and a dictionary containing
	the search info for rooms in a zone as prepared by the SearchReader procedures.

	An optional third argument overrides the format used in printing.

	It then outputs the data in the format readable by StuphMUD and the SearchReader,
	and additionally, prints the final '$' after any-or-all search records in said
	dictionary are formatted.

	'''
	order=list(sch.keys())
	order.sort() # by roomVNR

	for k in order:
		# Format this search to the file.  Does some magic on the dict.
		## Duplicate:
		A=sch.get(k)
		assert A

		S={}
		S.update(A)

		## Rearrange internals according to SEARCH_RECORD_FMT:
		S['ival0'], S['ival1'], S['ival2'], S['ival3'], \
				S['ival4'], S['ival5'] = A['intval']

		S['sval0'], S['sval1'], S['sval2'], S['sval3'], \
				S['sval4'], S['sval5'], S['sval6'], S['sval7'] = A['strval']

		S['lval0'], S['lval1'] = A['longval']

		## Output:
		print(fmt%S, file=out)

	print('$', file=out)

# DEFAULT_SEARCH_PATH='world/sch'
DEFAULT_SEARCH_PATH='tmp_sch'
DEFAULT_INSTALL_PATHKEY='STUPH_PATH'
DEFAULT_CLOBBER_OPT=False

def writeSearches(sch, path, overwrite=DEFAULT_CLOBBER_OPT):
	'Calculates the lowest zone in the given dictionary keys and formats the searches to filed path.'
	assert sch # Need key-values to decipher lowest zone NR

	lo=list(sch.keys())
	lo.sort() # descending: lowest last
	lo=int(lo[-1])/100

	fn=join(path, '%d.sch'%lo)

	if not overwrite:
		assert not exists(fn), 'Use overwrite=True when calling writeSearches!!'

	# Write the file
	return formatSearches(open(fn, 'w'), sch)

def loadNamedFile(fn):
	# Todo: Auto-detect file type (.sch file or another format)
	##  This is a potentially significant function, because it should be able to
	#   read multiple file formats (the .sch file, a file containing a python expression)

	sch=SearchReader(fn)
	sch.parseFile()

	return sch.consumeResult()

def doPrintSummary(searchFile, level=1):
	"""
	Print a description of the search file.

	The optional <level> argument can be an integer with a value that, when greater,
	will print more summary information than if a lesser value is specified:

		At level 0: no information is shown (useful for testing format)
		At level 1: displays the number of searchable rooms in this file

	"""
	sch=loadNamedFile(searchFile)

	# If level is 0, then we print nothing (but succeed this function)
	if level==1:
		print('%s: OK (%d searchable rooms)' % (basename(searchFile), len(sch)))


def doPrintAsDict(searchFile):
	pprint(loadNamedFile(searchFile))

def resolveInstallPath(path):
	'Finds and verifies the path.'
	path = path or \
		DEFAULT_SEARCH_PATH or \
			__import__('os').getenv(DEFAULT_INSTALL_PATHKEY)

	assert path, '--install-path option must be specified if STUPH_PATH environment is not set!'
	# assert __import__('os').path.exists(path)

def doInstall(searchFile, installPath, clobberSetting=None):
	installPath  = resolveInstallPath(installPath)
	searches     = loadNamedFile(searchFile)

	if clobberSetting in (True, False):
		writeSearches(searches, path, overwrite=clobberSetting)
	else:
		writeSearches(searches, path)

def processCmdln(cmdln):
	# Some settings.
	Path     = None  # No setting.
	Clobber  = None  # No setting.

	# Iterators.
	i=0
	n=len(cmdln)

	while i<n:
		a=cmdln[i]
		i+=1 # Next argument.

		# Do install operation inline.
		if a in ('-i', '--install'):
			assert i<n, str(a)+' <needs a search file>'
			doInstall(cmdln[i], Path, clobberSetting=Clobber)

			i+=1 # Consume the argument following.
			continue

		# Decipher install path.
		if a in ('-p', '--path', '--install-path'):
			assert i<n, str(a)+' <needs a path>'
			Path=cmdln[i]

			i+=1 # Consume the argument following.
			continue

		if a.startswith('--path='):
			Path=a[7:]  # this can be empty
			continue

		if a.startswith('--install-path='):
			Path=a[15:] # this can be empty
			continue

		# Order that the search file be parsed and printed in its internal form.
		if a in ('-d', '--dict', '--as-dict'):
			assert i<n, str(a)+' <needs a search file>'
			doPrintAsDict(cmdln[i])

			i+=1 # Consume the argument following.
			continue

		# Order that the search file be parsed and then printed in the formatted form.
		if a in ('-f', '--dump', '--dump-format'):
			assert i<n, str(a)+' <needs a search file>'
			formatSearches(stdout, loadNamedFile(cmdln[i]))

			i+=1 # Consume the argument following.
			continue

		# Order that the search file be parsed and only a level of summary be displayed.
		if a in ('-s', '--summary'):
			assert i<n, str(a)+' <needs a search file>'
			doPrintSummary(cmdln[i])

			i+=1 # Consume the argument following.
			continue

		if a.startswith('--summary='):
			# Use this to set the summary level
			assert i<n, str(a)+' <needs a search file>'
			level=int(a[:10:])

			doPrintSummary(cmdln[i], level=level)

			i+=1 # Consume the argument following.
			continue

		# Change clobber setting (if installation can overwrite files)
		if a in ('-X', '--overwrite', '--clobber'):
			Clobber=True
			continue

		if a in ('--no-overwrite', '--no-clobber'):
			Clobber=False
			continue

		if a.startswith('--clobber=') or a.startswith('--overwrite='):
			c=a[a.find('=')+1:].lower()

			# Decipher clobber setting:
			if c in ('true', 'yes', 'on'):
				Clobber=True
			else:
				assert c in ('false', 'no', 'off'), 'Unknown clobber argument: %r'%a
				Clobber=False

			continue

def main(cmdlnopts=None):
	if cmdlnopts is None:
		import sys
		cmdlnopts=getattr(sys, 'argv', [])[1:]

	try:
		processCmdln(cmdlnopts)

	except: # AssertionError:
		e=exc_info()
		tb=e[2]
		e=e[1]

		# Find last frame
		while tb and tb.tb_next:
			tb=tb.tb_next

		f=tb.tb_frame

		print(str(e), getline(f.f_code.co_filename, f.f_lineno).strip())

useDebugger=lambda:getenv('DEBUG', 'NO').upper() not in ('NO', 'OFF', 'FALSE')

if __name__=='__main__':
	if useDebugger():
		from pdb import runcall
		runcall(main)

	else:
		main()


##  Here's a script that could be useful.  It requires a path to searchlib.py and wldlib.py.
##  Put it in the bin directory, and call it something like 'searcheck'
#
#	#!/bin/bash
#
#	# Configure these things:
#	pylibdata_path="$HOME/pystuph/python/tools/libdata"
#	python_bin="/usr/bin/python" # or $HOME/python/python
#
#	# This is the default directory this script looks in when given a zone number.
#	stuphlib_worldsch="$HOME/stuph/lib/world/sch"
#
#	# These things don't need configuration.
#	searchlib_script="$pylibdata_path/searchlib.py"
#	stuphlib_schsuffix=".sch"
#
#	# Export PYTHON_PATH for it to propagate into the python executable process.
#	export PYTHON_PATH=$pylibdata_path
#
#	for zone in $*
#	do
#	    if [ -r $zone ]
#	    then
#	        search_file=$zone
#	    else
#	        search_file="$stuphlib_worldsch/$zone$stuphlib_schsuffix"
#	    fi
#
#	    # The PYTHON_PATH environment is exported above.
#	    $python_bin $searchlib_script --summary $search_file
#	done
#
##  This is how you might use the script:
#
#    searcheck 112 113 562 570 mysearch.sch my-other-search-file stuph/lib/world/sch/*.sch
#

