from getpass import getpass
from .services.security import hash_master_password
if __name__=='__main__':
    p=getpass('Create master password: '); c=getpass('Confirm master password: ')
    if p!=c: raise SystemExit('Passwords do not match.')
    print('\nAPP_PASSWORD_HASH='+hash_master_password(p))
