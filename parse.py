# -*- coding: cp1252 -*-
from bencode import *
import hashlib
import requests

def client():
    filename = 'E:\Downloads\BitTorrentClient\Anathema -- Vol18 [mininova].torrent'
    #filename = 'E:\Downloads\BitTorrentClient\debian-live-6.0.7-amd64-gnome-desktop.iso.torrent'
    bencodeMetaInfo = get_torrent_info(filename)
    #print(bencodeMetaInfo)
    announceKey = get_announce(bencodeMetaInfo)
    #print(announceKey)
    length = get_length(bencodeMetaInfo)
    #print(length)
    infoDict = get_info(bencodeMetaInfo)
    #print(infoDict)
    encodedInfo = bencode_info(infoDict)
    #encodedInfo = get_info_from_torrent(open(filename, 'rb').read())
    #print(encodedInfo)
    sha1HashedInfo = hashlib.sha1(encodedInfo).digest()
    announceUrl = announceKey + '?info_hash=' + sha1HashedInfo + '&peer_id=vincentlugli1.0sixty&port=5100&uploaded=0&downloaded=0&left=' + str(length) + '&compact=1'
    print(announceUrl)
    announceResponse = requests.get(announceUrl)
    print(announceResponse.status_code)
    print(bdecode(announceResponse.content))
    

def get_torrent_info(filename):
    metainfo_file = open(str(filename), 'rb')
    metainfo = bdecode(metainfo_file.read())
    info = metainfo['info']
    # torrentDir = info['name']
    return metainfo
    # metainfo_file.close()

    # info = metainfo['announce']
    # print info

    # info = metainfo['info']
    # torrentDir = info['name']
    # print torrentDir

    # This one I have output to a file called test.txt
    # info = metainfo['info']
    # print info

def get_announce(metainfo):
    return metainfo['announce']

def get_info(metainfo):
    return metainfo['info']

def get_length(metainfo):
    if ('files' in metainfo['info']):
        files = metainfo['info']['files']
        total = 0
        for filePart in files:
            total += filePart['length']
        return total        
    else:
        return metainfo['info']['length']

def bencode_info(info):
    encodedInfo = bencode(info)
    return encodedInfo

def get_info_from_torrent(torrent):
    print(torrent)
    infoLocation = torrent.find('info')
    done = False
    count = 1
    currChar = infoLocation+4
    result = ''
    while done == False:
        result += torrent[currChar]
        currChar += 1
        if (torrent[currChar] == 'i'):
            while (torrent[currChar] != 'e'):
                result += torrent[currChar]
                currChar += 1
            result += torrent[currChar]
            print('\nRESULT:' + result + '\n')
            currChar += 1
        elif (torrent[currChar] == 'l'):
            count += 1
        elif (torrent[currChar] == 'd'):
            count += 1
        elif (torrent[currChar].isdigit()):
            end = currChar + int(torrent[currChar]) + 2
            result += torrent[currChar : end]
            currChar = end
        elif (torrent[currChar] == 'e'):
            count -= 1
        if (count == 0):
            result += torrent[currChar]
            done = True
    print(result)
    return result

client()
