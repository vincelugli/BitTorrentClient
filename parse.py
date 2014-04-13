from bencode import *
torrentFile = 'C:\Users\Xialin\Documents\CS 3251\BitTorrentClient\debian-live-6.0.7-amd64-gnome-desktop.iso.torrent'
metainfo_file = open(str(torrentFile), 'rb')
metainfo = bdecode(metainfo_file.read())
info = metainfo['info']
torrentDir = info['name']
print info
metainfo_file.close()




# info = metainfo['announce']
# print info

# info = metainfo['info']
# torrentDir = info['name']
# print torrentDir

# This one I have output to a file called test.txt
# info = metainfo['info']
# print info