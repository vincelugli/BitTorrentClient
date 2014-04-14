from bencode import *
import hashlib
import requests

def client():
    bencodeMetaInfo = get_torrent_info('E:\Downloads\BitTorrentClient\Anathema -- Vol18 [mininova].torrent');
    announceKey = get_announce(bencodeMetaInfo)
    #print(announceKey)
    #print(bencodeMetaInfo)
    encodedInfo = bencode_info(bencodeMetaInfo)
    #print(encodedInfo)
    sha1HashedInfo = hashlib.sha1(encodedInfo).hexdigest()
    announceUrl = announceKey + '?port=5100&uploaded=0&downloaded=0&left=0&compact=1&peer_id=vincentlugli1.0sixty&info_hash=' + sha1HashedInfo
    #print(announceUrl)
    announceResponse = requests.get(announceUrl)
    print(announceResponse.text)
    

def get_torrent_info(filename):    
    torrentFile = filename;
    metainfo_file = open(str(torrentFile), 'rb')
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

def bencode_info(info):
    encodedInfo = bencode(info)
    return encodedInfo

client()
