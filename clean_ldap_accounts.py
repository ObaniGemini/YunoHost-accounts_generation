import os
import sys
from ldap3 import Server, Connection, ALL, SUBTREE

#
"""
	This script permits to create ldap accounts.
	It is meant ot be used to generate yuno host accounts from a large user database.
	YOU NEED TO BE EITHER ROOT OR SUPER-USER TO RUN THAT SCRIPT
	It requires :
		- python3
		- python3-ldap3
		- yunohost

	- init_ldap : initialize the connection to the ldap server
	- delete_generated_groups : if some groups/accounts have been created with this script, delete those
	- create_ldap_attributes : create the ldap attributes belonging to each account/group
	- create_ldap_group : Creates a ldap group with the accounts it has in it
	- generate_ldap_accounts : Main function : generates the accounts
	
	Accounts have a name, a first_name, a password, an ident, and belong to GROUP(S).
	These characteristics are present in a text file.
	The first line initializes the order of the accounts's informations (presented earlier).
	Apart from that line, each line defines a account.
	Accounts can belong to several groups (see example_csv.csv).
"""
#

OPTIONS = [['-h', '--help'], ['-a', '--address'], ['-p', '--password'], ['-u', '--user-admin']]
SERVER_ADDRESS = 'server_address'
ROOT_PASSWORD = 'root_password'
ADMIN_USER = 'admin'

PROTECTED_USERS = [ 'aaplis' ]
PROTECTED_GROUPS = [ 'all_users', 'visitors' ]

def check_args( i ):
    for j in range( 2 ):
        if OPTIONS[ i ][ j ] in sys.argv:
            return sys.argv.index(OPTIONS[i][j])
    return 0
    


def init_ldap():
    print('Init connection to ldap')
    global c, dn_base

    dn_base = os.popen('slapcat | grep dn:\ dc | cut -d " " -f2').read()
    dn_admin = os.popen('slapcat | grep dn:\ cn=' + ADMIN_USER).read().split('\n')

    if len( dn_admin ) == 0:
        print('Admin user "' + ADMIN_USER + '" doesn\'t exist !')
        exit( 1 )

    dn_admin = dn_admin[ 0 ].split(' ')[ 1 ]

    s = Server( host=SERVER_ADDRESS, get_info='ALL' )
    c = Connection( s, user=dn_admin, password=ROOT_PASSWORD )

    if not c.bind():
        print( 'Error in bind', c.result )
        exit( 1 )


def delete_generated_accounts():
    print('Deleting existing groups and accounts\n')

    to_delete = c.search( dn_base, search_filter='(|(cn=*)(uid=*))', search_scope=SUBTREE )
    j = 0
    for entry in c.response:
        entry_attr = entry[ 'dn' ].split(',')
        entry_attr = entry_attr[ 0 ]
        entry_attr = attr.split('=')

        if 'cn' == attr[ 0 ] and ( attr[ 1 ] in PROTECTED_USERS or attr[ 1 ] in PROTECTED_GROUPS ):
            continue

        if 'uid' == attr[ 0 ] and ( attr[ 1 ] in PROTECTED_USERS or attr[ 1 ] in PROTECTED_GROUPS ):
            continue

        print(entry)
        print(entry_attr)

        #c.delete( entry[ 'dn' ] )
        j += 1

    print('Deleted ' + str( j ) + ' groups and accounts')
    print('-------------------------------------\n')




###------SCRIPT EXECUTION------###

args = [ check_args( 0 ), check_args( 1 ), check_args( 2 ), check_args( 3 ) ]

if args[ 0 ]:
    print('\nUsage : command [OPTIONS] [ARGS]')
    print('Options :\n')
    print(' -h  --help      Display this message')
    print(' -a  --address   Set server\'s address and port (1 arg)')
    print(' -p  --password  Enter server\'s root password (1 arg)')
    print(' -u  --user-admin  Enter server\'s admin username (1 arg)')
    exit()
if args[ 1 ]:
    SERVER_ADDRESS = sys.argv[ args[ 1 ] + 1 ]
if args[ 2 ]:
    ROOT_PASSWORD = sys.argv[ args[ 2 ] + 1 ]
if args[ 3 ]:
    ADMIN_USER = sys.argv[ args[ 3 ] + 1 ]
    PROTECTED_USERS.append( ADMIN_USER )



init_ldap()
delete_generated_accounts()
os.system('yunohost app ssowatconf')
print('Done !')
c.unbind()
