#!/usr/bin/python3
#
# Find Freebase relation path between concept URL and answer for each question
#
# Use the Google API for Freebase mtaching answers in the subgraph of the
# question concept, storing all relations that do lead to one.
#
# Example:
#   mkdir d-freebase-rp
#   for split in devtest val trainmodel test; do echo $split; ./freebase_relpaths_g.py $split $googleapikey; done

from __future__ import print_function

from collections import Counter
import datalib
from multiprocessing import Pool
import json
from operator import itemgetter
import sys
import time
from urllib.request import urlopen


def walk_node(node, pathprefix, labels):
    relpaths = []
    for name, val in node['property'].items():
        for value in val['values']:
            if value['text'] in labels:
                relpaths.append(tuple(pathprefix + [name]))
            if 'property' in value:
                relpaths += walk_node(value, pathprefix + [name], labels)
    return relpaths


def get_question_rp(q):
    url = 'https://www.googleapis.com/freebase/v1/topic/en/' + q['freebaseKey']
    print(url)
    #time.sleep(1)
    global apikey
    urlresp = urlopen(url + '?key=' + apikey)
    resp = json.loads(urlresp.readall().decode('utf-8'))

    with open('x/' + q['freebaseKey'] + '.json', 'w') as f:
        print(json.dumps(resp, indent=4), file=f)

    path_labels = walk_node(resp, [], set(q['answers']))
    pl_counter = Counter(path_labels)
    pl_set = sorted([(pl, c) for pl, c in pl_counter.items()], key=itemgetter(1), reverse=True)

    print(url, pl_set)

    return {'qId': q['qId'],
            'relPaths': pl_set}


if __name__ == "__main__":
    global apikey
    split, apikey = sys.argv[1:]
    data = datalib.load_multi_data(split, ['main', 'd-freebase'])

    # XXX: We would like to write the JSON file as we go, but we need
    # to test for last element in save_json() and things would just
    # get too complicated too needlessly.

    pool = Pool(processes=2)
    #qrp = pool.map(get_question_rp, data.to_list())
    qrp = map(get_question_rp, data.to_list())
    pool.close()
    pool.join()

    with open('d-freebase-rp/%s.json' % (split,), 'w') as f:
        datalib.save_json(list(qrp), f)
