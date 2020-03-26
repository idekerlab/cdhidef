#!/usr/bin/env python

import os
import sys
import argparse
import traceback
import subprocess
import uuid
import shutil

DEFAULT_ERR_MSG = ('Did not get any clusters from HiDeF. This could be ' +
                   'due to a network that is too connected or ' +
                   ' the resolution parameter is too extreme\n')


def _parse_arguments(desc, args):
    """
    Parses command line arguments
    :param desc:
    :param args:
    :return:
    """
    help_fm = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(description=desc,
                                     formatter_class=help_fm)
    parser.add_argument('input',
                        help='Edge file in tab delimited format')
    parser.add_argument('--hidefcmd',
                        default='/opt/conda/lib/python3.7/site-packages/hidef/finder.py',
                        help='Path to hidef finder.py command')
    parser.add_argument('--tempdir', default='/tmp',
                        help='Directory needed to hold files temporarily for processing')
    return parser.parse_args(args)

def create_tmpdir(theargs):
    """
    :param theargs:
    :return:
    """
    tmpdir = os.path.join(theargs.tempdir, 'cdhidef_' + str(uuid.uuid4()))
    os.makedirs(tmpdir, mode=0o755)
    return tmpdir


def run_hidef_cmd(cmd):
    """
    Runs hidef command
    :param cmd_to_run: command to run as list
    :return:
    """
    p = subprocess.Popen(cmd,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)

    out, err = p.communicate()

    return p.returncode, out, err


def run_hidef(theargs):
    """
    :outdir: the output directory to comprehend the output link file
    :param graph: input file
    :param config_model: 'RB', 'RBER', 'CPM', 'Surprise', 'Significance'
    :param overlap: bool, whether to enable overlapping community detection
    :param directed
    :param deep
    :param interslice_weight
    :param resolution_parameter
    :return
    """
    cmdargs = []
    cmdargs.extend(['--g', theargs.input])
    if theargs.input is None or not os.path.isfile(theargs.input):
        sys.stderr.write(str(theargs.input) + ' is not a file')
        return 3

    if os.path.getsize(theargs.input) == 0:
        sys.stderr.write(str(theargs.input) + ' is an empty file')
        return 4

    tmpdir = create_tmpdir(theargs)
    try:
        cmdargs.extend(['-o', tmpdir])
        sys.stderr.write('Running ' + str(cmdargs) + '\n')
        sys.stderr.flush()
        cmdecode, cmdout, cmderr = run_hidef_cmd(cmdargs)

        if cmdecode != 0:
            sys.stderr.write('Command failed with non-zero exit code: ' +
                             str(cmdecode) + ' : ' + str(cmderr) + '\n')
            return 1

        if len(cmdout) > 0:
            sys.stderr.write('Output from cmd: ' + str(cmdout) + '\n')

        if len(cmderr) > 0:
            sys.stderr.write('Error output from cmd: ' + str(cmderr) + '\n')

        sys.stdout.flush()
        return 0
    finally:
        shutil.rmtree(tmpdir)


def main(args):
    """
    Main entry point for program
    :param args: command line arguments usually :py:const:`sys.argv`
    :return: 0 for success otherwise failure
    :rtype: int
    """
    desc = """
    Runs HiDeF on command line, sending output to standard
    out 
    """

    theargs = _parse_arguments(desc, args[1:])

    try:
        inputfile = os.path.abspath(theargs.input)

        return run_hidef(inputfile)

    except Exception as e:
        sys.stderr.write('\n\nCaught exception: ' + str(e))
        traceback.print_exc()
        return 2


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main(sys.argv))
