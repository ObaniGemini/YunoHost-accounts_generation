import os
import sys
import ldap
import ldap.modlist as modlist

#
"""
	This script permits to create ldap accounts.
	It is meant ot be used to generate yuno host accounts from a large user database.
	YOU NEED TO BE EITHER ROOT OR SUPER-USER TO RUN THAT SCRIPT
	It requires :
		- python3
		- python3-ldap
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

OPTIONS = [['-h', '--help'], ['-a', '--address'], ['-p', '--password']]
SERVER_ADDRESS = 'server_address'
ROOT_PASSWORD = 'root_password'

PROTECTED_USERS = [ 'admin', 'aaplis' ]
PROTECTED_GROUPS = [ 'all_users', 'visitors' ]

def check_args(i):
    for j in range(2):
        if OPTIONS[i][j] in sys.argv:
            return sys.argv.index(OPTIONS[i][j])
    return 0
    


def init_ldap( address, root_password ):
    print('Init connection to ldap')
    global l, dn_base
    l = ldap.initialize(address)
    dn_base = os.popen('slapcat | grep ^dn:\ dc | cut -d" " -f2').read()

    l.simple_bind_s('cn=admin,'+dn_base, root_password)



def delete_generated_accounts():
    print('Deleting existing groups and accounts\n')

    to_delete = l.search_s( dn_base, ldap.SCOPE_SUBTREE, '(|(cn=*)(uid=*))', None )
    j = 0
    for i in to_delete:
        j += 1
        if( i[ 1 ][ 'cn' ] not in PROTECTED_GROUPS && i[ 1 ][ 'uid' ] not in PROTECTED_USERS ):
            l.delete( i[ 0 ] )

    print('Deleted ' + str( j ) + ' groups and accounts')
    print('-------------------------------------\n')




###------SCRIPT EXECUTION------###

args = [ check_args(0), check_args(1), check_args(2)]

if args[ 0 ]:
    print('\nUsage : command [OPTIONS] [ARGS]')
    print('Options :\n')
    print(' -h  --help      Display this message')
    print(' -a  --address   Set server\'s address and port (1 arg)')
    print(' -p  --password  Enter server\'s root password (1 arg)')
    exit()
if args[ 1 ]:
    SERVER_ADDRESS = sys.argv[ args[ 1 ] + 1 ]
if args[ 2 ]:
    ROOT_PASSWORD = sys.argv[ args[ 2 ] + 1 ]



init_ldap( SERVER_ADDRESS, ROOT_PASSWORD )
delete_generated_accounts()
os.system('yunohost app ssowatconf')
print('Done !')
l.unbind_s()
