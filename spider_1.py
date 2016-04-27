"""
This script is used to show you how to use upwork api to search job info, for
more detail, please reference https://developers.upwork.com/

"""

import upwork
from pprint import pprint

PUBLIC_KEY = ""
SECRET_KEY = ""

def get_client():
    """Emulation of desktop app.
    Your keys should be created with project type "Desktop".
    Returns: ``upwork.Client`` instance ready to work.
    """
    print "Emulating desktop app"

    public_key = PUBLIC_KEY
    secret_key = SECRET_KEY

    client = upwork.Client(public_key, secret_key)
    verifier = raw_input(
        'Please enter the verification code you get '
        'following this link:\n{0}\n\n> '.format(
            client.auth.get_authorize_url()))

    print 'Retrieving keys.... '
    access_token, access_token_secret = client.auth.get_access_token(verifier)
    print 'OK'

    # For further use you can store ``access_toket`` and
    # ``access_token_secret`` somewhere
    client = upwork.Client(public_key, secret_key,
                          oauth_access_token=access_token,
                          oauth_access_token_secret=access_token_secret)
    return client

if __name__ == '__main__':
    if not PUBLIC_KEY or not SECRET_KEY:
        print "Please set the PUBLIC_KEY and SECRET_KEY in the python script"
    else:
        client = get_client()

        try:
            print "Get jobs"
            pprint(client.provider_v2.search_jobs({'q': 'python'}))
        except Exception, e:
            print "Exception at %s %s" % (client.last_method, client.last_url)
            raise e
