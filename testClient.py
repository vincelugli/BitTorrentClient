# -*- coding: utf-8 -*-
from socket import *
from bencode import *
import hashlib
import struct


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
        print('MULTIPLE FILES!')
        files = metainfo['info']['files']
        numFiles = len(files)
        total = 0
        sizeOfFiles = [numFiles]
        for filePart in files:
            sizeOfFiles.append(filePart['length'])
            total += filePart['length']
        sizeOfFiles.append(total)
        return sizeOfFiles
    else:
        print('SINGLE FILE!')
        return [1, metainfo['info']['length']]

def get_number_of_pieces(infoDict):
    return len(infoDict['pieces']) / 20

def get_length_of_piece(infoDict):
    return infoDict['piece length']

def bencode_info(info):
    encodedInfo = bencode(info)
    return encodedInfo



filename = 'E:\Downloads\BitTorrentClient\Anathema -- Vol18 [mininova].torrent'                # USE THIS TO TEST MULTIFILE TORRENT
bencodeMetaInfo = get_torrent_info(filename)
announceKey = get_announce(bencodeMetaInfo)
sizeOfFiles = get_length(bencodeMetaInfo)
isMultiFile = False
if (sizeOfFiles[0] > 1):
    isMultiFile = True
if (isMultiFile):
    length = sizeOfFiles[sizeOfFiles[0] + 1]
else:
    length = sizeOfFiles[sizeOfFiles[0]]
infoDict = get_info(bencodeMetaInfo)
numberOfPieces = get_number_of_pieces(infoDict)
lengthOfPiece = get_length_of_piece(infoDict)
encodedInfo = bencode_info(infoDict)
sha1HashedInfo = hashlib.sha1(encodedInfo).digest()


host = '128.61.89.77' 
port = 57894
sock = socket()
sock.connect((host, port))
test = struct.pack('>B19s8s20s20s', 19, 'BitTorrent protocol', '', sha1HashedInfo, '12345678901234567890')
sock.send(test)
