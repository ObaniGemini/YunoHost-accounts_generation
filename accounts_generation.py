import subprocess
import ldap
import ldap.modlist as modlist

#
"""
	This script permits to create ldap accounts.
	It is meant ot be used to generate yuno host accounts from a large user database.
	YOU NEED TO BE EITHER ROOT OR SUPER-USER TO RUN THAT SCRIPT
	It requires :
		- python2.7
		- python-subprocess32
		- python-ldap
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

def init_ldap(address, root_password):
    global l, dn_base, dn_groups, dn_users
    l = ldap.initialize(address)
    dn_base = subprocess.check_output('slapcat | grep ^dn:\ dc | cut -d" " -f2', shell=True)

    l.simple_bind_s('cn=admin,'+dn_base, root_password)
    dn_groups = ',ou=groups,'+dn_base
    dn_users = ',ou=users,'+dn_base




def delete_generated_accounts():
    print('Deleting existing groups and accounts')
    to_delete = l.search_s(dn_base, ldap.SCOPE_SUBTREE, 'description=*generated*', None)
    j = 0
    for i in to_delete:
        j += 1
        l.delete(i[0])

    print('Deleted '+str(j)+' groups and accounts')
    print('-------------------------------------')
    print(' ')




def create_ldap_attributes(attributes_list):
    attributes = {}
    for attribute in attributes_list:
        attributes[attribute[0]] = attribute[1]
    print(attributes)
    return attributes




def create_ldap_group(group_name, gid, attributes_list):
    dn='cn='+group_name+dn_groups
    ldif = modlist.addModlist(create_ldap_attributes(attributes_list))
    l.add_s(dn,ldif)
    print('Created '+group_name+' group')
    print('-------------------------------------')
    print(' ')




def generate_ldap_accounts(file_path, address, root_password):
    init_ldap(address, root_password)
    delete_generated_accounts()

### Retrieving the .csv file
    filin = open(file_path,'r')
    FILE = [list(line.replace('\n','')) for line in filin]
    filin.close()

    members = {}
    uid = 6000
    gid= 7000
    j = 0

    for line in FILE:
        LINE = ''
        for i in line:
            LINE += i
        LINE = LINE.split(';')

### If this is the first line, you should initialize the order of the collumns. e.g : groups | names | first_names | ...
        if FILE.index(line) == 0:
            groups_index = LINE.index('groups')
            name_index = LINE.index('name')
            first_name_index = LINE.index('first_name')
            password_index = LINE.index('password')
            ident_index = LINE.index('ident')
### Else, create the user
        else:
            j += 1
            groups = LINE[groups_index].split(',')
            name = LINE[name_index]
            first_name = LINE[first_name_index]
            password = LINE[password_index]
            ident = LINE[ident_index]
 
            dn='uid='+ident+dn_users
            uid += 1
            gid += 1

            for group in groups:
                if not group in members:
                    members[group] = []
                members[group].append(ident)


            attributes = create_ldap_attributes([['uidNumber', str(uid)], \
                        ['gidNumber', str(gid)], \
                        ['objectclass', ['mailAccount','inetOrgPerson','posixAccount']], \
                        ['uid', ident], \
                        ['maildrop', ident], \
                        ['cn', name+' '+first_name], \
                        ['displayName', name+' '+first_name], \
                        ['userPassword', password], \
                        ['sn', first_name], \
                        ['homeDirectory', '/home/'+ident], \
                        ['mail', ident+'@techno-sully.eu'], \
                        ['givenName', name], \
                        ['description', ['Compte de '+first_name+' '+name, 'generated']]])

            ldif = modlist.addModlist(attributes)
            l.add_s(dn,ldif)
    print(' ')
    print('Created '+str(j)+' accounts')
    print('-------------------------------------')
    print(' ')

    gid = 8000
    for group in members.keys():
        gid += 1
        create_ldap_group(group, gid, [['objectclass', ['top', 'posixGroup']], \
			['gidNumber', str(gid)], \
			['cn', group], \
			['description', [group+' group', 'generated']], \
			['memberuid', members[group]]])

    subprocess.call('yunohost app ssowatconf', shell=True)
    l.unbind_s()
    print('Done !')



###------SCRIPT EXECUTION------###

generate_ldap_accounts('file_path', 'server_address', 'root_password')
