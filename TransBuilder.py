import sys
import re
import Translator

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

__all__ = []
__version__ = 0.1
__date__ = '2019-12-26'
__updated__ = '2019-12-26'

DEBUG = 1
TESTRUN = 0
PROFILE = 0

line_num = {}

class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg
    def __str__(self):
        return self.msg
    def __unicode__(self):
        return self.msg

def main(argv=None): # IGNORE:C0111
    '''Command line options.'''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_license = '''%s

  Created by Hernan Theiler on %s.
  Copyright 2019 IBM Labs Haifa. All rights reserved.

USAGE
''' % ("RISC-V Hackaton", str(__date__))

#     try:
    # Setup argument parser
    parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument("input", help="Input XML file")
    parser.add_argument("output", help="Output XML file")
    parser.add_argument("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %(default)s]")
    parser.add_argument('-V', '--version', action='version', version=program_version_message)

    # Process arguments
    args = parser.parse_args()
    
    rdw = Translator.Interface()
    trn = Translator.Translator(isLoad=True)
    rdw.load_file(trn, args.input)
    trn.build()
    rdw.save_file(trn, args.output)

    return 0

if __name__ == "__main__":
    sys.exit(main())