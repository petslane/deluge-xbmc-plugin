'''
Created on Mar 30, 2012

@author: Iulian Postaru
'''

from io import BytesIO
import gzip

def unGzip(gzipContent) :
    buf = BytesIO(gzipContent)
    unz = gzip.GzipFile(fileobj=buf)
    return unz.read()
