import os
import sys

#
"""
	This script permits to create ldap accounts.
	It is meant ot be used to generate yuno host accounts from a large user database.
	YOU NEED TO BE EITHER ROOT OR SUPER-USER TO RUN THAT SCRIPT
	It requires :
		- python3
		- yunohost
	
	Accounts have a first_name, a last_name, a password and an username.
	These characteristics are present in a text file.
	The first line initializes the order of the accounts's informations (presented earlier).
	Apart from that line, each line defines a account.
	Accounts can belong to several groups (see example_csv.csv).
"""
#

OPTIONS = [['-h', '--help'], ['-f', '--file'], ['-d', '--domain']]
FILE_PATH = 'file_path'
DOMAIN_NAME = ''

DEFAULT_GROUPS = [ 'all_users', 'visitors' ] ###Groups that can't be removed
DEFAULT_USERS = [ 'aapplis', 'admin' ]       ###Users that can't be removed


def check_args( i ):
    for j in range( 2 ):
        if OPTIONS[ i ][ j ] in sys.argv:
            return sys.argv.index( OPTIONS[ i ][ j ] )
    return 0



def create_user( username, first_name, last_name, email, password ):
    os.system('yunohost user create "' + username + '" -f "' + first_name + '" -l "' + last_name + '" -m "' + email + '" -p "' + password + '"')


def remove_user( username ):
    os.system('yunohost user delete "' + username + '"')


def create_group( group_name ):
    os.system('yunohost user group create "' + group_name + '"')


def add_users_group( group_name, users_list ):
    os.system('yunohost user group update "' + group_name + '" -a ' + ' '.join( users_list ))



def generate_accounts():
    users_list = os.popen('yunohost user list | grep username | cut -d ":" -f 2').read().split()
    groups_list = os.popen('yunohost user group list | grep : | grep -v members | grep -v groups | cut -d ":" -f 1 ').read().split()

    for group in DEFAULT_GROUPS:
        print('Keeping ' + group + ' group')
        groups_list.remove( group )


    for group in groups_list:
        os.system('yunohost user group delete ' + group)

### Retrieving the .csv file
    filin = open( FILE_PATH, 'r' )
    FILE = [ list( line.replace('\n','') ) for line in filin ]
    filin.close()

    groups = {}
    groups_created = 0
    created = 0
    updated = 0
    removed = 0

    first_line = True

    if( len( FILE[ len( FILE ) - 1 ] ) < 5 ): ###Remove last line in case it's empty
        FILE.pop()

    for line in FILE:
        LINE = ''.join( line ).replace('"', '')
        LINE = LINE.split(';')

### If this is the first line, you should initialize the order of the collumns. e.g : groups | names | first_names | ...
        if first_line:
            groups_name_idx = LINE.index('groups')
            first_name_idx  = LINE.index('first_name')
            last_name_idx   = LINE.index('last_name')
            password_idx    = LINE.index('password')
            username_idx    = LINE.index('username')
            first_line = False
            continue


### Else, check the user and its group
        groups_name = LINE[ groups_name_idx ].lower().split(',')
        first_name  = LINE[ first_name_idx ]
        last_name   = LINE[ last_name_idx ]
        password    = LINE[ password_idx ]
        username    = LINE[ username_idx ]

        for group_name in groups_name:
            if( group_name in DEFAULT_GROUPS ):
                continue

            elif( group_name not in groups_list ):
                create_group( group_name )
                groups_list.append( group_name )
                groups[ group_name ] = []
                groups_created += 1
            elif group_name not in groups:
                create_group( group_name )
                groups[ group_name ] = []

        if( username not in users_list ): ### Add those who joined us
            create_user( username, first_name, last_name, '"' + username.replace('"', '') + '@' + DOMAIN_NAME + '"', password )
            for group_name in groups_name:
                groups[ group_name ].append( '"' + username + '"' )
            created += 1
        else: ###Update those who still are with us
            users_list.remove( username )
            for group_name in groups_name:
                groups[ group_name ].append( '"' + username + '"' )
            updated += 1

### Remove those who left us
    for user in users_list:
        if user in DEFAULT_USERS:
            print("Keeping " + user + " user")
            continue
        remove_user( user )
        removed += 1

    print(' ')
    print('Created ' + str( groups_created ) + ' groups')
    print('Created ' + str( created ) + ' accounts')
    print('Updated ' + str( updated ) + ' accounts')
    print('Removed ' + str( removed ) + ' accounts')
    print('-------------------------------------')
    print(' ')

    for group in groups.keys():
        add_users_group( group, groups[ group ] )

    os.system('yunohost app ssowatconf')
    print('Done !')





###------SCRIPT EXECUTION------###

args = [ check_args( 0 ), check_args( 1 ), check_args( 2 ) ]

if args[ 0 ]:
    print('\nUsage : command [OPTIONS] [ARGS]')
    print('Options :\n')
    print(' -h  --help      Display this message')
    print(' -f  --file      Set the csv file path for current usage (1 arg)')
    exit()
if args[ 1 ]:
    FILE_PATH = sys.argv[ args[ 1 ] + 1 ]
if args[ 2 ]:
    DOMAIN_NAME = sys.argv[ args[ 2 ] + 1 ]
else:
    domains = os.popen('yunohost domain list').read().split(':')[ 1 ].replace(' ', '').split("\n")
    domains.remove('')

    for i in range( len( domains ) ):
        if( domains[ i ].startswith('-') ):
            domains[ i ] = domains[ i ][1:]

    for i in range( len( domains ) ):
        if( domains[ i ].startswith('-') ):
            domains[ i ] = domains[ i ][1:]

    chosen = 0

    while( chosen == None or chosen <= 0 or chosen > len( domains ) ):
        for i in range( len( domains ) ):
            print( str( i + 1 ) + ' ' + domains[ i ] )
        chosen = int(input('Please choose one of the following domains\n'))

    DOMAIN_NAME = domains[ chosen - 1 ]


generate_accounts()
