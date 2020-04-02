#!/usr/bin/env python

import os
import sys
import argparse
import traceback
import subprocess
import uuid
import csv
import shutil

DEFAULT_ERR_MSG = ('Did not get any clusters from HiDeF. Not sure'
                   ' what is going on\n')

X_PREFIX = 'x'


class Formatter(argparse.ArgumentDefaultsHelpFormatter,
                argparse.RawDescriptionHelpFormatter):
    pass


def _parse_arguments(desc, args):
    """
    Parses command line arguments
    :param desc:
    :param args:
    :return:
    """
    parser = argparse.ArgumentParser(description=desc,
                                     formatter_class=Formatter)
    parser.add_argument('input',
                        help='Edge file in tab delimited format')
    parser.add_argument('--n', type=int,
                        help='explore the maximum resolution '
                             'parameter until cluster number '
                             'is close enough to this value. '
                             'Increase this number to get more '
                             'smaller clusters')
    parser.add_argument('--t', type=float, default=0.1,
                        help='(inversed) density of sampling '
                             'the resolution parameter; decrease '
                             'this number to introduce more transient '
                             'clusters (with longer running time);')
    parser.add_argument('--k', type=int, default=5,
                        help='a parameter to pre-filter instable '
                             'clusters')
    parser.add_argument('--j', type=float, default=0.75,
                        help='a jaccard index cutoff')
    parser.add_argument('--minres', type=float, default=0.001,
                        help='minimum resolution parameter')
    parser.add_argument('--maxres', type=float, default=100.0,
                        help='maximum resolution parameter')
    parser.add_argument('--s', type=float, default=1.0,
                        help='a subsample parameter')
    parser.add_argument('--ct', default=75, type=int,
                        help='threshold in collapsing cluster')
    parser.add_argument('--alg', default='louvain',
                        choices=['louvain', 'leiden'],
                        help='add the option to use leiden algorithm')
    parser.add_argument('--hidefcmd',
                        default='hidef_finder.py',
                        help='Path to hidef_finder.py command')
    parser.add_argument('--tempdir', default='/tmp',
                        help='Directory needed to hold files temporarily for processing')
    return parser.parse_args(args)


def create_tmpdir(theargs):
    """
    Creates temp directory for hidef output with
    a unique name of format cdhidef_<UUID>

    :param theargs: Holds attributes from argparse
    :type theargs: `:py:class:`argparse.Namespace`
    :return: Path to temp directory
    :rtype: str
    """
    tmpdir = os.path.join(theargs.tempdir, 'cdhidef_' + str(uuid.uuid4()))
    os.makedirs(tmpdir, mode=0o755)
    return tmpdir


def run_hidef_cmd(cmd):
    """
    Runs hidef command as a command line process
    :param cmd_to_run: command to run as list
    :type cmd_to_run: list
    :return: (return code, standard out, standard error)
    :rtype: tuple
    """
    p = subprocess.Popen(cmd,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)

    out, err = p.communicate()

    return p.returncode, out, err


def get_max_node_id(nodes_file):
    """
    Examines the 'nodes_file' passed in and finds the value of
    highest node id.

    It is assumed the 'nodes_file' a tab delimited
    file of format:

    <CLUSTER NAME> <# NODES> <SPACE DELIMITED NODE IDS> <SCORE>

    :param nodes_file:
    :type nodes_file: Path to to nodes file from hidef output
    :return: highest node id found
    :rtype: int
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
    Given a row from nodes file from hidef output the members
    of the clusters by parsing the <SPACE DELIMITED NODE IDS>
    as mentioned in :py:func:`#get_max_node_id` description.

    The output is written to `out_stream` for each node id
    in format:

    <cur_node_id>,<node id>,c-m;

    :param out_stream:
    :type out_stream: file like object
    :param row: Should be a line from hidef nodes file parsed
                by :py:func:`csv.reader`
    :type row: iterator
    :param cur_node_id: id of cluster that contains the nodes
    :type cur_node_id: int
    :return: None
    """
    for node in row[2].split(' '):
        out_stream.write(str(cur_node_id) + ',' +
                         node + ',c-m;')


def update_cluster_node_map(cluster_node_map, cluster, max_node_id):
    """
    Updates 'cluster_node_map' which is in format of

    <cluster name> => <node id>

    by adding 'cluster' to 'cluster_node_map' if it does not
    exist

    :param cluster_node_map: map of cluster names to node ids
    :type cluster_node_map: dict
    :param cluster: name of cluster
    :type cluster: str
    :param max_node_id: current max node id
    :type max_node_id: int
    :return: (new 'max_node_id' if 'cluster' was added otherwise 'max_node_id',
              id corresponding to 'cluster' found in 'cluster_node_map')
    :rtype: tuple
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
    Writes out links between clusters in COMMUNITYDETECTRESULT format
    as noted in :py:func:`#convert_hidef_output_to_cdaps`

    using hidef edge file set in 'edge_file' that is expected to
    be in this tab delimited format:

    <SOURCE CLUSTER> <TARGET CLUSTER> <default>

    This function converts the <SOURCE CLUSTER> <TARGET CLUSTER>
    to new node ids (leveraging 'cluster_node_map')

    and writes the following output:

    <SOURCE CLUSTER NODE ID>,<TARGET CLUSTER NODE ID>,c-c;

    to the 'out_stream'

    :param out_stream: output stream
    :type out_stream: file like object
    :param edge_file: path to hidef edges file
    :type edge_file: str
    :return: None
    """
    with open(edge_file, 'r') as csvfile:
        linereader = csv.reader(csvfile, delimiter='\t')
        for row in linereader:
            out_stream.write(str(cluster_node_map[row[0]]) + ',' +
                             str(cluster_node_map[row[1]]) + ',c-c;')


def convert_hidef_output_to_cdaps(out_stream, tempdir):
    """
    Looks for x.nodes and x.edges in `tempdir` directory
    to generate output in COMMUNITYDETECTRESULT format:
    https://github.com/idekerlab/communitydetection-rest-server/wiki/COMMUNITYDETECTRESULT-format

    This method leverages

    :py:func:`#write_members_for_row`

    and

    :py:func:`#write_communities`

    to write output

    :param out_stream: output stream to write results
    :type out_stream: file like object
    :param tempdir:
    :type tempdir: str
    :return: None
    """
    nodefile = os.path.join(tempdir, X_PREFIX + '.nodes')
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
    edge_file = os.path.join(tempdir, X_PREFIX + '.edges')
    write_communities(out_stream, edge_file, cluster_node_map)
    out_stream.write('\n')
    return None


def build_optional_arguments(theargs):
    """
    Builds list of optional arguments and values

    :param theargs: Holds attributes from argparse
    :type theargs: `:py:class:`argparse.Namespace`
    :return: arguments for hidef in list of str objects
    :rtype: list
    """
    cmdargs = []
    if theargs.n is not None:
        cmdargs.extend(['--n', str(theargs.n)])

    cmdargs.extend(['--t', str(theargs.t)])
    cmdargs.extend(['--k', str(theargs.k)])
    cmdargs.extend(['--j', str(theargs.j)])
    cmdargs.extend(['--minres', str(theargs.minres)])
    cmdargs.extend(['--maxres', str(theargs.maxres)])
    cmdargs.extend(['--s', str(theargs.s)])
    cmdargs.extend(['--ct', str(theargs.ct)])
    cmdargs.extend(['--alg', theargs.alg])
    return cmdargs


def run_hidef(theargs, out_stream=sys.stdout,
              err_stream=sys.stderr):
    """
    Runs hidef command line program and then converts
    output to CDAPS compatible format that is output to
    standard out.

    :param theargs: Holds attributes from argparse
    :type theargs: `:py:class:`argparse.Namespace`
    :param out_stream: stream for standard output
    :type out_stream: file like object
    :param err_stream: stream for standard error output
    :type err_stream: file like object
    :return: 0 upon success otherwise error
    :rtype: int
    """
    cmdargs = []
    cmdargs.extend([theargs.hidefcmd, '--g', theargs.input,
                    '--skipclug', '--skipgml'])
    cmdargs.extend(build_optional_arguments(theargs))

    if theargs.input is None or not os.path.isfile(theargs.input):
        err_stream.write(str(theargs.input) + ' is not a file')
        return 3

    if os.path.getsize(theargs.input) == 0:
        err_stream.write(str(theargs.input) + ' is an empty file')
        return 4

    tmpdir = create_tmpdir(theargs)
    try:
        outval = os.path.join(tmpdir, X_PREFIX)
        cmdargs.extend(['--o', outval])
        err_stream.write('Running ' + str(' '.join(cmdargs)) + '\n')
        err_stream.flush()
        cmdecode, cmdout, cmderr = run_hidef_cmd(cmdargs)

        if cmdecode != 0:
            err_stream.write('Command failed with non-zero exit code: ' +
                             str(cmdecode) + ' : ' + str(cmderr) + '\n')
            return 1

        if len(cmdout) > 0:
            err_stream.write('Output from cmd: ' + str(cmdout) + '\n')

        if len(cmderr) > 0:
            err_stream.write('Error output from cmd: ' + str(cmderr) + '\n')

        try:
            convert_hidef_output_to_cdaps(out_stream, tmpdir)
        except FileNotFoundError as fe:
            err_stream.write('No output from hidef: ' + str(fe) + '\n')
            return 5
        return 0
    finally:
        err_stream.flush()
        out_stream.flush()
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
        return run_hidef(theargs, sys.stdout, sys.stderr)
    except Exception as e:
        sys.stderr.write('\n\nCaught exception: ' + str(e))
        traceback.print_exc()
        return 2


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main(sys.argv))
