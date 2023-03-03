'''
Created on Apr 10, 2012

@author: iulian.postaru
'''

class Filter(object):
    
    name = ''
    count = 0
    filterType = ''

    def __init__(self, name, count, filterType = ''):
        self.name = name
        self.count = count
        self.filterType = filterType
        #if (self.name == ''):
        #    self.name = 'No Label'
        
    def __str__(self):
        return str(self.name) + ' (' + str(self.count) + ')'