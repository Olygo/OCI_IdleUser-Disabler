# coding: utf-8

# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# name: OCI_IdleUser_Disabler.py
# task: retrieve all users in a IAM Domain,
#       retrieve users last connection date, 
#       disable users not connected since 60 days (default)
#
# Author: Florian Bonneville
# Version: 1.0 - December 04th, 2023
#
# Disclaimer: 
# This script is an independent tool developed by 
# Florian Bonneville and is not affiliated with or 
# supported by Oracle. It is provided as-is and without 
# any warranty or official endorsement from Oracle
#

import os
import oci
import argparse
from datetime import datetime
from modules.identity import create_signer
from modules.utils import green, yellow, red, clear, print_info, print_output

script_path = os.path.abspath(__file__)
script_name = (os.path.basename(script_path))[:-3]
analysis_start = datetime.now()

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# get command line arguments
# - - - - - - - - - - - - - - - - - - - - - - - - - -

def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument('-cs', action='store_true', default=False, dest='is_delegation_token', 
                        help='Use CloudShell Delegation Token for authentication')
    parser.add_argument('-cf', action='store_true', default=False, dest='is_config_file', 
                        help='Use local OCI config file for authentication')
    parser.add_argument('-cfp', default='~/.oci/config', dest='config_file_path', 
                        help='Path to your OCI config file, default: ~/.oci/config')
    parser.add_argument('-cp', default='DEFAULT', dest='config_profile', 
                        help='config file section to use, default: DEFAULT')
    parser.add_argument('-endpoint', default='', dest='endpoint', required=True,
                        help='Identity Domain URL')
    parser.add_argument('-days', default=60, dest='days', type=int, 
                        help='Number of days of inactivity')
    parser.add_argument('-dryrun',action='store_true', default=False, dest='dryrun', 
                        help='Evaluate users without deactivating')
    
    return parser.parse_args()

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# clear shell screen
# - - - - - - - - - - - - - - - - - - - - - - - - - -

clear()

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# retrieve arguments
# - - - - - - - - - - - - - - - - - - - - - - - - - -

cmd = parse_arguments()
days_history = 60 if not cmd.days else cmd.days

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# print header
# - - - - - - - - - - - - - - - - - - - - - - - - - -

print(green(f"\n{'*'*94:94}"))
print_info(green, 'Analysis', 'started', script_name)

if cmd.dryrun:
    print_info(yellow, 'Dry Run', 'session', 'no change applied')

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# oci authentication
# - - - - - - - - - - - - - - - - - - - - - - - - - -

config, signer, oci_tname=create_signer(cmd.config_file_path, 
                                        cmd.config_profile, 
                                        cmd.is_delegation_token, 
                                        cmd.is_config_file)

identity_client=oci.identity.IdentityClient(
                config=config)

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# init oci service clients
# - - - - - - - - - - - - - - - - - - - - - - - - - -

identity_domain_client=oci.identity_domains.IdentityDomainsClient(config, cmd.endpoint)

print(green(f"{'*'*94:94}\n"))

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# retrieve users data
# - - - - - - - - - - - - - - - - - - - - - - - - - -

user_rank = 0
users_data = {}
users_disabled = {}

users=identity_domain_client.list_users(
                                        attribute_sets=["all"],
                                        sort_by="userName",
                                        sort_order="ASCENDING",
                                        count=1000
                                        )

for user in users.data.resources:
    user_rank=user_rank+1
    try:
        last_login = user.urn_ietf_params_scim_schemas_oracle_idcs_extension_user_state_user.previous_successful_login_date
        last_login = "None" if last_login is None else last_login

        users_data[user_rank] = {
        'ocid': user.ocid,
        'last_login': last_login,
        'state': '',
        'active': 'True' if user.active else 'False',
        'days': '',
        'name': user.user_name,
        'domain': user.domain_ocid,
        'created': user.meta.created
        }
        # convert the timestamp string to a datetime object
        timestamp = datetime.strptime(last_login, "%Y-%m-%dT%H:%M:%S.%fZ")

        # get the current datetime
        now = datetime.utcnow()  # Use utcnow() to ensure consistency with the provided timestamp

        # calculate the difference between the current datetime and the provided timestamp
        time_difference = now - timestamp

        # check if the difference is greater than x days
        if time_difference.days > days_history:
            users_data[user_rank]['state'] = 'Dormant'
            users_data[user_rank]['days'] = time_difference.days
        else:
            users_data[user_rank]['state'] = 'Active'
            users_data[user_rank]['days'] = time_difference.days

    except:
        last_login = "None"
        users_data[user_rank] = {
        'ocid': user.ocid,
        'last_login': last_login,
        'state': 'Inactive',
        'active': 'True' if user.active else 'False',
        'days': '-',
        'name': user.user_name,
        'domain': user.domain_ocid,
        'created': user.meta.created
        }

print(f"{'#':<5} {'user':<40} {'last connection':<30} {'active':<10} {'state':<10} {'hist/days':<13} {'ocid':<40}")

for user_rank, user_data in users_data.items():

    if user_data['active'] == 'False':
        color = red
    elif user_data['state'] in ['Dormant', 'Inactive']:
        color = yellow
    else:
        color = green

    print_output(color, user_rank, user_data)

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    # disable inactive users
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    # https://docs.oracle.com/en/cloud/paas/identity-cloud/rest-api/op-admin-v1-userstatuschanger-id-put.html
    if user_data['active'] == 'True':
        if user_data['state'] in ['Dormant', 'Inactive']:
            users_disabled[user_rank] = {
                'ocid': user_data['ocid'],
                'last_login': user_data['last_login'],
                'name': user_data['name'],
                'active': user_data['active'],
                'state': user_data['state'],
                'days': user_data['days'],
                'ocid': user_data['ocid']
                }

            if not cmd.dryrun:
                put_user_status_changer_response = identity_domain_client.put_user_status_changer(
                    user_status_changer_id=user_data['ocid'],
                    user_status_changer=oci.identity_domains.models.UserStatusChanger(
                    schemas=["urn:ietf:params:scim:schemas:oracle:idcs:UserStatusChanger"], # comment this line out will display an error showing the schema to use !
                    active=False))

                users_disabled[user_rank] = {
                    'ocid': user_data['ocid'],
                    'last_login': put_user_status_changer_response.data.meta.last_modified,
                    'name': user_data['name'],
                    'active': 'True' if put_user_status_changer_response.data.active else 'False',
                    'state': user_data['state'],
                    'days': user_data['days'],
                    'ocid': user_data['ocid']
                    }

if users_disabled:
    print(f"\n\n{'#':<5} {'user disabled':<40} {'updated_on':<30} {'active':<10} {'state':<10} {'hist/days':<13} {'ocid':<40}")
    for user_rank, user_data in users_disabled.items():
        print_output(red, user_rank, user_data)
    if cmd.dryrun:
        print()
        print_info(yellow, 'DRYN RUN', 'SESSION', 'NO CHANGE APPLIED')
        print()
    else:
        print()
else:
    print()