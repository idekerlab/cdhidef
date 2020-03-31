#!/usr/bin/env python

import os
import sys
import argparse
import traceback
import subprocess
import uuid
import csv
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
                        default='hidef_finder.py',
                        help='Path to hidef_finder.py command')
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


def get_max_node_id(nodes_file):
    """

    :param nodes_file:
    :return:
    """
    maxval = None
    with open(nodes_file, 'r') as csvfile:
        linereader = csv.reader(csvfile, delimiter='\t')
        for row in linereader:
            for node in row[2].split(' '):
                if maxval is None:
                    maxval = int(node)
                    continue
                curval = int(node)
                if curval > maxval:
                    maxval = curval
    return maxval


def write_members_for_row(out_stream, row, cur_node_id):
    """

    :param out_stream:
    :param row:
    :param cur_node_id:
    :return:
    """
    for node in row[2].split(' '):
        out_stream.write(str(cur_node_id) + ',' +
                         node + ',c-m;')

def update_cluster_node_map(cluster_node_map, cluster, max_node_id):
    """

    :param cluster_node_map:
    :param cluster:
    :param max_node_id:
    :return:
    """
    if cluster not in cluster_node_map:
        max_node_id += 1
        cluster_node_map[cluster] = max_node_id
        cur_node_id = max_node_id
    else:
        cur_node_id = cluster_node_map[cluster]
    return max_node_id, cur_node_id


def write_communities(out_stream, edge_file, cluster_node_map):
    """

    :param out_stream:
    :param edgefile:
    :return:
    """
    with open(edge_file, 'r') as csvfile:
        linereader = csv.reader(csvfile, delimiter='\t')
        for row in linereader:
            out_stream.write(str(cluster_node_map[row[0]]) + ',' +
                             str(cluster_node_map[row[1]]) + ',c-c;')


def convert_hidef_output_to_cdaps(out_stream, tmpdir):
    """
    Looks for x.nodes and x.edges in `tmpdir` directory
    to generate output in COMMUNITYDETECTRESULT format:
    https://github.com/idekerlab/communitydetection-rest-server/wiki/COMMUNITYDETECTRESULT-format

    which is
    :param out_stream: output stream to write results
    :type out_stream: file like object
    :param tmpdir:
    :type tmpdir: str
    :return:
    """
    nodefile = os.path.join(tmpdir, 'x.nodes')
    max_node_id = get_max_node_id(nodefile)
    cluster_node_map = {}
    with open(nodefile, 'r') as csvfile:
        linereader = csv.reader(csvfile, delimiter='\t')
        for row in linereader:
            max_node_id, cur_node_id = update_cluster_node_map(cluster_node_map,
                                                               row[0],
                                                               max_node_id)
            write_members_for_row(out_stream, row,
                                  cur_node_id)
    edge_file = os.path.join(tmpdir, 'x.edges')
    write_communities(out_stream, edge_file, cluster_node_map)
    out_stream.write('\n')
    return None


def run_hidef(theargs):
    """

    :param theargs:
    :return:
    """
    cmdargs = []
    cmdargs.extend([theargs.hidefcmd, '--g', theargs.input])
    if theargs.input is None or not os.path.isfile(theargs.input):
        sys.stderr.write(str(theargs.input) + ' is not a file')
        return 3

    if os.path.getsize(theargs.input) == 0:
        sys.stderr.write(str(theargs.input) + ' is an empty file')
        return 4

    tmpdir = create_tmpdir(theargs)
    try:
        outval = os.path.join(tmpdir, 'x')
        cmdargs.extend(['--o', outval])
        sys.stderr.write('Running ' + str(' '.join(cmdargs)) + '\n')
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

        convert_hidef_output_to_cdaps(sys.stdout, tmpdir)
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

        return run_hidef(theargs)

    except Exception as e:
        sys.stderr.write('\n\nCaught exception: ' + str(e))
        traceback.print_exc()
        return 2


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main(sys.argv))
