#!/usr/bin/env python
import json
import os
import sys
import argparse
import traceback
import subprocess
import uuid
import csv
import shutil
import copy

import cdhidef
from ndex2.cx2 import RawCX2NetworkFactory

DEFAULT_ERR_MSG = ('Did not get any clusters from HiDeF. Not sure'
                   ' what is going on\n')

X_PREFIX = 'x'

CDRES_KEY_NAME = 'communityDetectionResult'

NODE_CX_KEY_NAME = 'nodeAttributesAsCX2'

ATTR_DEC_NAME = 'attributeDeclarations'

PERSISTENCE_COL_NAME = 'HiDeF_persistence'


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
                        help='Target community number. Explore the'
                             'maximum resolution parameter until the '
                             'number of generated communities at this '
                             'resolution is close enough to this value. '
                             'Increase to get more smaller communities')
    parser.add_argument('--k', type=int, default=5,
                        help='Persistence threshold. Increase to '
                             'delete unstable clusters, and get fewer '
                             'communities')
    parser.add_argument('--maxres', type=float, default=25.0,
                        help='Maximum resolution parameter. '
                             'Increase to get more smaller communities')
    parser.add_argument('--p', default=75, type=int,
                        help='Consensus threshold. Threshold of '
                             'collapsing community graph and'
                             'choose geneas for each community')
    parser.add_argument('--alg', default='leiden',
                        choices=['louvain', 'leiden'],
                        help='Chose to use Louvain or the newer Leiden '
                             'algorithm. Must be "louvain" or "leiden"')
    parser.add_argument('--hidefcmd',
                        default='hidef_finder.py',
                        help='Path to hidef_finder.py command')
    parser.add_argument('--tempdir', default='/tmp',
                        help='Directory needed to hold files temporarily for processing')
    parser.add_argument('--csvmaxfieldsize', type=int, default=100000000,
                        help='Sets maximum field size for csv parser')
    parser.add_argument('--numthreads', type=int, default=4,
                        help='Sets number of threads to use. '
                             'If 0 or negative, then '
                             'value of multiprocessing.cpu_count() is used')
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


def update_persistence_map(persistence_node_map, node_id, persistence_val):
    """

    :param persistence_node_map:
    :param node_id:
    :param persistence_val:
    :return:
    """
    if node_id not in persistence_node_map:
        persistence_node_map[node_id] = persistence_val


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
    out_stream.write('",')


def write_persistence_node_attribute(out_stream, persistence_map):
    """

    :param out_stream:
    :param persistence_map:
    :return:
    """
    out_stream.write('"' + NODE_CX_KEY_NAME + '": {')
    out_stream.write('"' + ATTR_DEC_NAME + '": [{')
    out_stream.write('"nodes": { "' + PERSISTENCE_COL_NAME +
                     '": { "d": "integer", "a": "p1", "v": 0}}}],')
    out_stream.write('"nodes": [')
    is_first = True
    for key in persistence_map:
        if is_first is False:
            out_stream.write(',')
        else:
            is_first = False
        out_stream.write('{"id": ' + str(key) + ',')
        out_stream.write('"v": { "p1": ' + str(persistence_map[key]) + '}}')

    out_stream.write(']}}')


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
    persistence_map = {}
    out_stream.write('{"communityDetectionResult": "')
    with open(nodefile, 'r') as csvfile:
        linereader = csv.reader(csvfile, delimiter='\t')
        for row in linereader:
            max_node_id, cur_node_id = update_cluster_node_map(cluster_node_map,
                                                               row[0],
                                                               max_node_id)
            update_persistence_map(persistence_map, cur_node_id, row[-1])
            write_members_for_row(out_stream, row,
                                  cur_node_id)
    edge_file = os.path.join(tempdir, X_PREFIX + '.edges')
    write_communities(out_stream, edge_file, cluster_node_map)
    write_persistence_node_attribute(out_stream, persistence_map)
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

    cmdargs.extend(['--k', str(theargs.k)])
    cmdargs.extend(['--maxres', str(theargs.maxres)])
    cmdargs.extend(['--p', str(theargs.p)])
    cmdargs.extend(['--alg', theargs.alg])
    cmdargs.extend(['--numthreads', str(theargs.numthreads)])
    return cmdargs


def update_hcx_annotations(hierarchy, interactome_id='00000000-0000-0000-0000-000000000000'):
    """
    This method updates the given network hierarchy with specific HCX annotations. These annotations
    are associated with the interactome ID and the NDEx server where the interactome resides.

    :param hierarchy: The network hierarchy that needs to be updated with HCX annotations.
    :type hierarchy: `~ndex2.cx2.CX2Network`
    :param interactome_id: The unique ID (UUID) of the interactome that is associated with the hierarchy.
    :type interactome_id: str
    :return: The updated hierarchy with the HCX annotations.
    :rtype: `~ndex2.cx2.CX2Network`
    """
    hierarchy_copy = copy.deepcopy(hierarchy)
    hierarchy_copy.add_network_attribute('HCX::interactionNetworkUUID', str(interactome_id))
    hierarchy_copy.remove_network_attribute('HCX::interactionNetworkName')
    return hierarchy_copy


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
                    '--skipgml'])
    cmdargs.extend(build_optional_arguments(theargs))

    if theargs.input is None or not os.path.isfile(theargs.input):
        err_stream.write(str(theargs.input) + ' is not a file')
        return 3

    if os.path.getsize(theargs.input) == 0:
        err_stream.write(str(theargs.input) + ' is an empty file')
        return 4

    csv.field_size_limit(theargs.csvmaxfieldsize)
    tmpdir = create_tmpdir(theargs)
    try:
        err_stream.write('Running ' + str(' '.join(cmdargs)) + '\n')
        err_stream.flush()
        try:
            factory = RawCX2NetworkFactory()
            path = os.path.join(os.path.dirname(cdhidef.__file__), 'hierarchy.cx2')
            net = factory.get_cx2network(path)
            hier = update_hcx_annotations(net)
            json.dump(hier.to_cx2(), out_stream)
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
    out in new 
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
