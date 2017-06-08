#!/usr/bin/env python3
# Copyright 2016 ETH Zurich
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Import ISD/AD data from topology files
"""

# Stdlib
import glob
import os
import sys
from os.path import dirname as d

WEB_SCION_DIR = d(d(os.path.abspath(__file__)))  # noqa
SCION_ROOT_DIR = d(d(WEB_SCION_DIR))  # noqa
SCION_PYTHON_ROOT_DIR = os.path.join(SCION_ROOT_DIR, 'python')  # noqa
sys.path.insert(0, WEB_SCION_DIR)  # noqa
sys.path.insert(0, SCION_ROOT_DIR)  # noqa
sys.path.insert(0, SCION_PYTHON_ROOT_DIR)  # noqa

# Set up the Django environment
os.environ['DJANGO_SETTINGS_MODULE'] = 'web_scion.settings.private'  # noqa

# External packages
import django
from django.db import transaction

import yaml

# SCION
from lib.defines import GEN_PATH, PROJECT_ROOT
from lib.topology import Topology

# Django app imports
from ad_manager.models import AD, ISD
from django.contrib.auth.models import User

WEB_SCION_DIR = os.path.join(PROJECT_ROOT, 'web_scion')
sys.path.insert(0, WEB_SCION_DIR)  # noqa
django.setup()  # noqa

GEN_PATH = os.path.join(PROJECT_ROOT, GEN_PATH)


def clear_everything():
    print('> Deleting everything...')
    ISD.objects.all().delete()


def add_users():
    """
    Create a superuser ('admin') and an ordinary user ('user1')
    """
    try:
        User.objects.get(username='admin').delete()
    except User.DoesNotExist:
        pass
    User.objects.create_superuser(username='admin', password='admin', email='')
    print('> Superuser was created')

    try:
        User.objects.get(username='user1').delete()
    except User.DoesNotExist:
        pass
    User.objects.create_user(username='user1', password='user1', email='')
    print('> User (user1) was created')


def get_topology(file):
    """
    Reads in the topology file and serves the relevant part of that
    to the visualization extension.
    :returns: A list of links extracted from the topology file.
    :rtype: list
    """
    with open(file, 'r') as stream:
        try:
            topo_dict = yaml.load(stream)
            return topo_dict
        except (yaml.YAMLError, KeyError):
            return []  # TODO: give user feedback


def reload_data_from_files(topology_files, on_the_fly_refs=False):
    ad_num = len(topology_files)
    print("> {} yaml topology files found".format(ad_num))

    isds = {}
    as_topos = []
    as_topo_dicts = {}

    same_as_ids = False
    # Iterate over all topology files and fill some data structures
    for topo_file in topology_files:
        topo_dict = get_topology(topo_file)
        topology = Topology.from_dict(topo_dict)
        isds[topology.isd_as[0]] = None

        if not same_as_ids and topology.isd_as[1] in as_topo_dicts:
            same_as_ids = True
        as_topo_dicts[topology.isd_as[1]] = topo_dict
        as_topos.append(topology)

        as_topos = sorted(as_topos, key=lambda t: t.isd_as[1])
    assert len(as_topos) == ad_num

    if same_as_ids:
        id_map = {}
        print("> Several ASes with identical IDs are found. Currently, this "
              "case is not supported. Renumerating ASes...")
        ad_id = 1
        for topo in as_topos:
            id_map[(topo.ad_id, topo.isd_id)] = ad_id
            topo.ad_id = ad_id
            ad_id += 1

        # Fixing routers
        for topo in as_topos:
            routers = topo.get_all_border_routers()
            for router in routers:
                neighbor_id = router.interface.neighbor_ad
                new_neighbor_id = id_map[(neighbor_id,
                                          router.interface.neighbor_isd)]
                router.interface.neighbor_ad = new_neighbor_id

    # Create ISD objects
    for isd_id in sorted(
            isds.keys()):  # sorted(isds.keys()):  # TODO: Does it need sorting?
        isd = ISD(id=isd_id)
        isd.save()
        isds[isd_id] = isd

    # First, save all add ASes to avoid IntegrityError
    report_ranges = {int(ad_num / 10.0 * x): x * 10 for x in range(1, 11)}
    for i, as_topo in enumerate(as_topos, start=1):
        if i in report_ranges:
            print("{}%".format(report_ranges[i]))
        AD.objects.update_or_create(as_id=as_topo.isd_as[1],
                                    isd=isds[as_topo.isd_as[0]],
                                    is_core_ad=as_topo.is_core_as)
    transaction.commit()
    print("> ASes instances were added")

    # Second, add routers, servers, etc.
    for as_topo in as_topos:
        ad = AD.objects.get(id=as_topo.isd_as[1], isd=isds[
            as_topo.isd_as[0]])  # getitem[0] = self._isd, [1] = self._as
        topo_dict = as_topo_dicts[ad.id]
        ad.fill_from_topology(topo_dict, auto_refs=on_the_fly_refs)
        print('> AS {} is loaded'.format(ad))
    transaction.commit()
    transaction.set_autocommit(True)


def reload_data():
    transaction.set_autocommit(True)
    clear_everything()
    add_users()

    # Add model instances
    # get any topology.yml for the AS, as all are identical and
    # there is no authoritative one
    yaml_path = os.path.join(GEN_PATH, 'ISD*', 'AS*', 'endhost', 'topology.yml')
    topology_files = glob.glob(yaml_path)

    reload_data_from_files(topology_files)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'users':
        add_users()
    else:
        reload_data()
