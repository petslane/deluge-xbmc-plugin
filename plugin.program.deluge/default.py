import urllib, sys, os, re, time
import xbmcaddon, xbmcplugin, xbmcgui, xbmc, xbmcvfs
from datetime import datetime

# Plugin constants 
__addonname__ = "DelugeXBMCPlugin"
__addonid__   = "plugin.program.deluge"
__addon__     = xbmcaddon.Addon(id=__addonid__)
__language__  = __addon__.getLocalizedString
if hasattr(xbmcvfs, 'translatePath'):
	__cwd__       = xbmcvfs.translatePath( __addon__.getAddonInfo('path') )
	__profile__   = xbmcvfs.translatePath( __addon__.getAddonInfo('profile') )
else:
	__cwd__       = xbmc.translatePath( __addon__.getAddonInfo('path') )
	__profile__   = xbmc.translatePath( __addon__.getAddonInfo('profile') )
__icondir__   = os.path.join( __cwd__, 'resources', 'icons' )

# Shared resources 
BASE_RESOURCE_PATH = os.path.join( __cwd__, 'resources', 'lib' )
sys.path.append (BASE_RESOURCE_PATH)

UT_ADDRESS = __addon__.getSetting('ip')
UT_PORT = __addon__.getSetting('port')
UT_PASSWORD = __addon__.getSetting('pwd')

url = 'http://' + UT_ADDRESS + ':' + UT_PORT + '/json'
baseurl = url

from resources.lib.utilities import *
import json
from resources.lib.DelugeWebUI import DelugeWebUI
from resources.lib.Filter import Filter
from resources.lib.States import States

addon_handle    = int(sys.argv[1])

webUI = DelugeWebUI(url)
	
def isTorrentListable(torrent, stateName):
	if torrent.state == stateName:
		return True
	if stateName == States.All:
		return True
	if stateName == States.Finished and torrent.progress == 100:
		return True
	if stateName == States.Unfinished and torrent.progress > 0 and torrent.progress < 100:
		return True
	if stateName == States.Unstarted and torrent.progress == 0:
		return True
	if stateName == States.Active and (torrent.state == States.Downloading or torrent.state == States.Seeding):
		return True
	return False

def translateTorrentState(state):
	if state == 'Downloading':
		return getTranslation(32200) or 'Downloading'
	elif state == 'Queued':
		return getTranslation(32201) or 'Queued'
	elif state == 'Paused':
		return getTranslation(32202) or 'Paused'
	elif state == 'Seeding':
		return getTranslation(32203) or 'Seeding'

def listTorrents(torrentList, stateName):
	restoreSession()
	mode = 1
	for torrentInfo in torrentList:
		if isTorrentListable(torrentInfo, stateName):
			if torrentInfo.state == States.Paused:
				thumb = os.path.join(__icondir__, 'deluge_paused.png')
			elif torrentInfo.state == States.Downloading:
				thumb = os.path.join(__icondir__, 'deluge_downloading.png')
			elif torrentInfo.state == States.Queued:
				thumb = os.path.join(__icondir__, 'deluge_queued.png')
			elif torrentInfo.state == States.Seeding:
				thumb = os.path.join(__icondir__, 'deluge_seeding.png')
			else:
				thumb = os.path.join(__icondir__, 'unknown.png')
			url = baseurl
			name = '[B]{name}[/B]   [LIGHT]{state} | {progress_label} {progress_value}% | {size_label} {size_value} | {down_label} {down_value} | {up_label} {up_value} | {eta_label} {eta_value}[/LIGHT]'.format(
				name=torrentInfo.name,
				state=translateTorrentState(torrentInfo.state),
				progress_label=getTranslation(30001),
				progress_value=torrentInfo.progress,
				size_label=getTranslation(30002),
				size_value=torrentInfo.getStrSize(),
				down_label=getTranslation(30003),
				down_value=torrentInfo.downloadPayloadRate,
				up_label=getTranslation(30004),
				up_value=torrentInfo.uploadPayloadRate,
				eta_label=getTranslation(30005),
				eta_value=torrentInfo.getStrEta(),
			)
			addTorrent(name, url, mode, thumb, torrentInfo.torrentId, torrentInfo.timeAdded)
			mode = mode + 1
	#xbmc.executebuiltin('Container.SetViewMode(500)') # 55 - List; 
	xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_DATEADDED)
	xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_TITLE)
	xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)

def performAction(selection):
	restoreSession()
	dialog = xbmcgui.Dialog()
	selectedAction = dialog.select(getTranslation(32001), [getTranslation(32002), getTranslation(32003), getTranslation(32007), getTranslation(32008), getTranslation(32019), getTranslation(32011), getTranslation(32012)])
	if selectedAction == 0:
		webUI.pauseTorrent(selection)
	if selectedAction == 1:
		webUI.resumeTorrent(selection)
	if selectedAction == 2:
		removeTorrent(selection, False)
	if selectedAction == 3:
		removeTorrent(selection, True)
	if selectedAction == 4:
		labels = webUI.getLabels()
		labelDialog = xbmcgui.Dialog()
		selectedLabel = labelDialog.select(getTranslation(32020), labels)
		if selectedLabel != -1:
			webUI.labelSetTorrent(selection, labels[selectedLabel])
	if selectedAction == 5:
		webUI.pauseAllTorrents()
	if selectedAction == 6:
		webUI.resumeAllTorrents()
	xbmc.executebuiltin('Container.Refresh')

def removeTorrent(selection, removeData):
	if __addon__.getSetting('confirmTorrentDeleting'):
		dialog = xbmcgui.Dialog()
		if dialog.yesno(getTranslation(32021), getTranslation(32022)):
			webUI.removeTorrent(selection, removeData)
	else:
		webUI.removeTorrent(selection, removeData)

def restoreSession():
	try:
		if webUI.checkSession() == False:
			if webUI.login(UT_PASSWORD):
				if not webUI.connected():
					webUI.connectToFirstHost()
	except urllib.error.URLError:
		dialog = xbmcgui.Dialog()
		ret = dialog.yesno(__addonname__ + ' ' + getTranslation(32100), getTranslation(32101), getTranslation(32102))
		if ret == True:
			__addon__.openSettings()
		sys.exit()
	
def pauseAll():
	restoreSession()
	webUI.pauseAllTorrents()
	xbmc.executebuiltin('Container.Refresh')

def resumeAll():
	restoreSession()
	webUI.resumeAllTorrents()
	xbmc.executebuiltin('Container.Refresh')
    
def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
            params=sys.argv[2]
            cleanedparams=params.replace('?','')
            if (params[len(params)-1]=='/'):
                    params=params[0:len(params)-2]
            pairsofparams=cleanedparams.split('&')
            param={}
            for i in range(len(pairsofparams)):
                    splitparams={}
                    splitparams=pairsofparams[i].split('=')
                    if (len(splitparams))==2:
                            param[splitparams[0]]=splitparams[1]

    return param

def getTranslation(translationId):
    return __language__(translationId)

def addTorrent(name, url, mode, iconimage, hashNum, timeAdded):
    u = sys.argv[0]+"?url="+urllib.parse.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.parse.quote_plus(name)+"&hashNum="+str(hashNum)
    point = xbmcgui.ListItem(name)
    point.setInfo('video', {
        'dateadded': datetime.fromtimestamp(timeAdded).isoformat().replace('T', ' '),
        'title': name
    })
    point.setArt({ 'thumb': iconimage })
    rp = "XBMC.RunPlugin(%s?mode=%s)"
    point.addContextMenuItems([(getTranslation(32011), rp % (sys.argv[0], 1000)), (getTranslation(32012), rp % (sys.argv[0], 1001))], replaceItems=True)
    ok = xbmcplugin.addDirectoryItem(handle=addon_handle,url=u,listitem=point,isFolder=False)
	
def addFilters(filter, mode, label):
	iconimage = ''
	if filter.name == '':
		displayName = '[LIGHT]%s[/LIGHT]  [B](%s)[/B]' % (getTranslation(30009), filter.count)
	else:
		displayName = '%s [B](%s)[/B]' % (filter.name, filter.count)
	u = sys.argv[0] + "?url=&mode=" + str(mode) + "&filterName=" + urllib.parse.quote_plus(filter.name) + "&filterCount=" + str(filter.count)
	if label:
		u = u + "&labelName=" + urllib.parse.quote_plus(label.name) + "&labelCount=" + str(label.count)
	ok = True
	liz = xbmcgui.ListItem(displayName)
	liz.setInfo( type="Video", infoLabels = {"Title": displayName} )
	if filter.filterType == 'label':
		liz.setArt({ 'icon': 'DefaultTags.png', 'thumb': iconimage })
	else:
		liz.setArt({ 'icon': 'DefaultFolder.png', 'thumb': iconimage })

	rp = "XBMC.RunPlugin(%s?mode=%s)"
	liz.addContextMenuItems([(getTranslation(32011), rp % (sys.argv[0], 1000)), (getTranslation(32012), rp % (sys.argv[0], 1001))], replaceItems=True)
	ok = xbmcplugin.addDirectoryItem(handle=addon_handle, url=u, listitem=liz, isFolder=True)

def addStateFilters(states, label):
	for state in states:
		if state.count > 0:
			addFilters(state, 7007, label)

def listFilters():
	restoreSession()
	addStateFilters(webUI.getStateFilters(), None)
	
	labels = webUI.getLabelsFilters()
	for label in labels:
		if label.count > 0:
			addFilters(label, 5005, label)
	
	xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)
		
def getParams():
	global url, name, mode, hashNum, filterName, filterCount, labelName, labelCount
	try:
		url = urllib.parse.unquote_plus(params['url'])
	except:
		pass
	try:
		name = urllib.parse.unquote_plus(params['name'])
	except:
		pass
	try:
		mode = int(params['mode'])
	except:
		pass
	try:
		hashNum = urllib.parse.unquote_plus(params['hashNum'])
	except:
		pass
	try:
		filterName = urllib.parse.unquote_plus(params['filterName'])
	except:
		pass
	try:
		filterCount = int(urllib.parse.unquote_plus(params['filterCount']))
	except:
		pass
	try:
		labelName = urllib.parse.unquote_plus(params['labelName'])
	except:
		labelName = ''
	try:
		labelCount = int(urllib.parse.unquote_plus(params['labelCount']))
	except:
		labelCount = 0

xbmc.log( '-----------------------------------Deluge.Plugin-Started---', xbmc.LOGINFO )

params = get_params()
url = None
name = None
mode = 0
hashNum = None
filterName = None

getParams()
	
if mode == 0:
    listFilters()
	
if mode == 7007:
	restoreSession()
	if labelCount > 0:
		torrents = webUI.getTorrentListByLabel(labelName)
	else:
		torrents = webUI.getTorrentList()
	listTorrents(torrents, filterName)

if mode == 5005:
	restoreSession()
	torrents = webUI.getTorrentListByLabel(filterName)
	states = webUI.getStateList(torrents)
	label = Filter(labelName, labelCount)
	if len(torrents) > int(__addon__.getSetting('torrentCountForStateGrouping')):
		addStateFilters(states, label)
	else:
		listTorrents(torrents, States.All)
	xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)
	

elif mode == 1000:
    pauseAll()

elif mode == 1001:
    resumeAll()

#elif mode == 1004:
#    limitSpeeds()

#elif mode == 1005:
#    addFiles()

elif 0 < mode < 1000:
    performAction(hashNum)

#TODO: To change mode from int to string. To add a enum class for mode.
