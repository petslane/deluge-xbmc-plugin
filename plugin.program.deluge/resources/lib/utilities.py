from http.cookiejar import LWPCookieJar
import urllib.request
import sys, os
from base64 import b64encode
import xbmc

__addonname__ = sys.modules[ "__main__" ].__addonname__
__addon__     = sys.modules[ "__main__" ].__addon__
__language__  = sys.modules[ "__main__" ].__language__

# base paths
BASE_DATA_PATH = sys.modules[ "__main__" ].__profile__
BASE_RESOURCE_PATH = sys.modules[ "__main__" ].BASE_RESOURCE_PATH
COOKIEFILE = os.path.join( BASE_DATA_PATH, "uTorrent_cookies" )

def _create_base_paths():
    """ creates the base folders """
    if ( not os.path.isdir( BASE_DATA_PATH ) ):
        os.makedirs( BASE_DATA_PATH )
_create_base_paths()

def MultiPart(fields,files,ftype) :
    Boundary = '----------ThIs_Is_tHe_bouNdaRY_---$---'
    CrLf = '\r\n'
    L = []

    ## Process the Fields required..
    for (key, value) in fields:
        L.append('--' + Boundary)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    ## Process the Files..
    for (key, filename, value) in files:
        L.append('--' + Boundary)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        ## Set filetype based on .torrent or .nzb files.
        if ftype == 'torrent':
            filetype = 'application/x-bittorrent'
        else:
            filetype = 'text/xml'
        L.append('Content-Type: %s' % filetype)
        ## Now add the actual Files Data
        L.append('')
        L.append(value)
    ## Add End of data..
    L.append('--' + Boundary + '--')
    L.append('')
    ## Heres the Main stuff that we will be passing back..
    post = CrLf.join(L)
    content_type = 'multipart/form-data; boundary=%s' % Boundary
    ## Return the formatted data..
    return content_type, post

class Client(object):
    def __init__(self, address='localhost', port='8080', user=None, password=None):
        self.url = "http://%s:%s/gui/" % (address, port)

        self.jar = LWPCookieJar(COOKIEFILE)
        try:
            self.jar.load()
        except:
            pass

        cookieHandler = urllib.request.HTTPCookieProcessor(self.jar)
        passwordManager = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        passwordManager.add_password(None, self.url, user, password)
        authHandler = urllib.request.HTTPBasicAuthHandler(passwordManager)
        self.opener = urllib.request.build_opener([authHandler, cookieHandler])


    def HttpCmd(self, urldta, postdta=None, content=None):
        xbmc.log( "%s::HttpCmd - url: %s" % ( __addonname__, urldta ), xbmc.LOGDEBUG )
        
        headers = {
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1) chromeframe/4.0'
        }
        if content != None:
            headers['content-type'] = content
            headers['Content-length'] = len(postdta)

        req = urllib.request.Request(
            urldta, 
            data=postdta, 
            headers=headers,
            method="POST"
        )

        response = urllib.request.urlopen(req, timeout=10)
        
        link = response.read().decode('utf-8')

        self.jar.save(ignore_discard=True)

        return link
