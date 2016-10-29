#!/usr/bin/env python

import requests
from requests import Request,Session
import json
import re
import time
import optparse
import ctypes

STD_INPUT_HANDLE = -10
STD_OUTPUT_HANDLE= -11
STD_ERROR_HANDLE = -12

FOREGROUND_BLACK = 0x0
FOREGROUND_BLUE = 0x01 # text color contains blue.
FOREGROUND_GREEN= 0x02 # text color contains green.
FOREGROUND_RED = 0x04 # text color contains red.
FOREGROUND_INTENSITY = 0x08 # text color is intensified.

BACKGROUND_BLUE = 0x10 # background color contains blue.
BACKGROUND_GREEN= 0x20 # background color contains green.
BACKGROUND_RED = 0x40 # background color contains red.
BACKGROUND_INTENSITY = 0x80 # background color is intensified.

class Color:
    ''' See http://msdn.microsoft.com/library/default.asp?url=/library/en-us/winprog/winprog/windows_api_reference.asp
    for information on Windows APIs.'''
    std_out_handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
    
    def set_cmd_color(self, color, handle=std_out_handle):
        """(color) -> bit
        Example: set_cmd_color(FOREGROUND_RED | FOREGROUND_GREEN | FOREGROUND_BLUE | FOREGROUND_INTENSITY)
        """
        bool = ctypes.windll.kernel32.SetConsoleTextAttribute(handle, color)
        return bool
    
    def reset_color(self):
        self.set_cmd_color(FOREGROUND_RED | FOREGROUND_GREEN | FOREGROUND_BLUE)
    
    def print_red_text(self, print_text):
        self.set_cmd_color(FOREGROUND_RED | FOREGROUND_INTENSITY)
        print print_text
        self.reset_color()
        
    def print_green_text(self, print_text):
        self.set_cmd_color(FOREGROUND_GREEN | FOREGROUND_INTENSITY)
        print print_text
        self.reset_color()
    
    def print_blue_text(self, print_text): 
        self.set_cmd_color(FOREGROUND_BLUE | FOREGROUND_INTENSITY)
        print print_text
        self.reset_color()
        
# These two values will have to be updated periodically using a proxy such as
# Burp, or ZAP. Go through the account recovery process once and find the
# POST request for https://www.facebook.com/ajax/login/help/identify.php?ctx=recover&dpr=1.
# POST request for https://twitter.com/account/begin_password_reset.
# It will have both of the needed values.
LSD = 'AVreKqty'
DATR = 'zZkRWLpGmvKdQcAOnLNZ_o9n'

_TWITTER_SESS= 'BAh7DSIKZmxhc2hJQzonQWN0aW9uQ29udHJvbGxlcjo6Rmxhc2g6OkZsYXNo%250ASGFzaHsABjoKQHVzZWR7ACIJcHJycCIAOg9jcmVhdGVkX2F0bCsIaO%252BzBFgB%250AOgxjc3JmX2lkIiUxMGVkMDIzYWZiODM0MGNhYTE4Y2RjODVhNmQxN2NlYjoH%250AaWQiJWIxZjA1MTQ0NDJiNzJmOGZlZmY3ZjY0ZWIwOTI4NGQxOghwcnNpCDoI%250AcHJ1bCsHbcyIZToIcHJpaQc%253D--4b198b7b6ff655a9bb04bf32f5028c8aedb45ea6'
GUEST_ID = 'v1%3A147498389812344406'
_GA='GA1.2.1355008855.1477665501'
PID='v3:1477665494207147188947700'
AUTH_TOKEN = '1b3c593415a83e1830e5b12d5e3df358acd14b9e'
# Compiled regular expressions to get the user's name and profile picture from
# the returned data.
re_pic = re.compile(r'pic.php\?cuid=(.*?)&amp')
re_usr = re.compile(r'<div class="fsl fwb fcb">(.*?)</div>')

# Necessary variables DO NOT MODIFY these.
fb = 'https://www.facebook.com/'
pic_url = '{0}profile/pic.php?cuid='.format(fb)
recover_url = '{0}ajax/login/help/identify.php?ctx=recover&dpr=1'.format(fb)
headers_facebook = {
    'Cookie': 'datr={0}'.format(DATR)
}
data_facebook = 'lsd={0}&email={1}&did_submit=Search&__user=0&__a=1'


twi = 'https://twitter.com/'
begin_reset_url = '{0}account/begin_password_reset'.format(twi)
headers_twitter = {
    'Accept-Encoding': 'gzip, deflate', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8','User_Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.0 Safari/537.36','Cookie': 'guest_id={0};_ga={1};_gat=1;pid="{2}";_twitter_sess={3}'.format(GUEST_ID,_GA,PID,_TWITTER_SESS)
}
data_twitter = 'authenticity_token={0}&account_identifier={1}' 
# Determine if an email address is associated with an account on facebook.
def check_facebook(sess, email):
    resp = sess.post(recover_url, headers=headers_facebook, data=data_facebook.format(LSD, email))
    content = resp.content

    if content.startswith('for (;;);'):
        content = content[9:]

    try:
        content = json.loads(content)

    except:
        return None

    urls = content.get('onload')
    if urls is None:
        return None

    return [u[24:].replace('\\', '').replace('"', '') for u in urls]

# Determine if an email address is associated with an account on twitter.
def check_twitter(email):
    sess = Session()

    req = Request('POST', begin_reset_url, data=data_twitter.format(AUTH_TOKEN,email), headers=headers_twitter)
    prepped = req.prepare()

    # do something with prepped.headers
    del prepped.headers['User_Agent']

    resp = sess.send(prepped)
    return resp.status_code

# Get the user account information from the URL.
def get_user(sess, url):
    resp = sess.get(url)
    name = re_usr.search(resp.content)
    pic = re_pic.search(resp.content)

    if name is not None:
       name = name.group(1)

    if pic is not None:
       pic = '{0}{1}'.format(pic_url, pic.group(1))

    clr.print_green_text('{0} - {1}'.format(name, pic))


# Test all email in the text file which you provided. Modify this as
# needed to test the email you want.

def main():
    parser = optparse.OptionParser('usage: %prog [options]')
    parser.add_option('-f', '--file', dest='names_file', default=None, type='string', help='email file.')
    (options, args) = parser.parse_args()
    if options.names_file == None and options.output == None:
        parser.print_help()
        sys.exit(0)

    rfile = open(options.names_file)
    global sess_fb,sess_twi,clr
    sess_fb = None
    sess_twi = None
    
    for email in rfile:
        clr = Color()
        print('')
        clr.print_red_text(email)
        sess_fb = requests.Session()
        sess_fb.get(fb)
        accounts_fb = check_facebook(sess_fb, email)
        if accounts_fb is not None:
            clr.print_green_text('=' * 10 + 'facebook' + '='*10)

            for account in accounts_fb:
                get_user(sess_fb, '{0}{1}'.format(fb, account))
    
        accounts_twi = check_twitter(email)
        if accounts_twi == 302:
            clr.print_blue_text('=' * 10 + 'twitter' + '='*10)
            clr.print_blue_text(accounts_twi)
            clr.print_blue_text("the email has registed twitter")

        time.sleep(5)
    rfile.close()

if __name__ == '__main__':
    main()
