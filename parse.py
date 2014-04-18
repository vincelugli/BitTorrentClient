from bencode import *
from struct import *
import hashlib
import requests
import socket

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
    numberOfPieces = len(infoDict['pieces']) / 20
    #print(numberOfPieces)
    encodedInfo = bencode_info(infoDict)
    #print(encodedInfo)
    sha1HashedInfo = hashlib.sha1(encodedInfo).digest()
    peerID = 'vincentlugli1.0sixty'
    announceUrl = announceKey + '?info_hash=' + sha1HashedInfo + '&peer_id=' + peerID + '&port=5100&uploaded=0&downloaded=0&left=' + str(length) + '&compact=1'
    #print(announceUrl)
    announceResponse = requests.get(announceUrl)
    #print(announceResponse.status_code)
    content = bdecode(announceResponse.content)
    #print(content)
    peerList = content['peers']
    #print(peerList)
    peerIPs = get_peer_IP_list(peerList)
    peerPorts = get_peer_port_list(peerList)
    #print(peerIPs)
    #print(peerPorts)

    # Actual connections begin here.

    # Handshake
    
    handshakeMessage = pack('b19s8s20s20s', 19, 'BitTorrent protocol', '', sha1HashedInfo, peerID)
    #print(handshakeMessage)

    sock = socket.socket()
    host = peerIPs[1]
    port = peerPorts[1]
    
    sock.connect((host, port))
    sock.send(handshakeMessage)
    handshakeResponse = sock.recv(1024)
    
    # Message Passing (keep-alive, choke, unchoke, interested, not-interested, have, etc...)

    keepAlive = True
    isChocked = False
    isInterested = False
    
    # Cases for message: keep-alive, choke, unchoke, interested, not-interested, have, bitfield, request, piece, cancel, and port
    
    options = {0 : 'choke',
               1 : 'unchoke',
               2 : 'interested',
               3 : 'not interested',
               4 : 'have',
               5 : 'bitfield',
               6 : 'request',
               7 : 'piece',
               8 : 'cancel',
               9 : 'port', }

    print('---------------')
    messageLengthStr = sock.recv(4)
    messageLengthInt = 0
    for x in range(0, len(messageLengthStr)):
        messageLengthInt += ord(messageLengthStr[x])
    print('length: ' + str(messageLengthInt))

    clientHasPieces = []
    
    if (messageLengthInt != 0):
        messageID = ord(sock.recv(1))
        print('Message: ' + options[messageID])
        if (messageLengthInt == 0):
            keepAlive = True
        elif (messageID == 0):
            isChocked = True
        elif (messageID == 1):
            isChocked = False
        elif (messageID == 2):
            isInterested = True
        elif (messageID == 3):
            isInterested = False
        else:
            if (messageID == 4):    # HAVE
                content = sock.recv(messageLengthInt-1)
                # not sure what to do with the piece index here...
                print('Piece Index: ' + content)
            elif (messageID == 5):  # BITFIELD
                bitfield = bin(ord(sock.recv(messageLengthInt-1)))
                print('BitField: ' + bitfield)
                # Looking to see which pieces the client has.
                for x in range(2, numberOfPieces+2):
                    if (bitfield[x] == '1'):
                        clientHasPieces.append(True)
                    else:
                        clientHasPieces.append(False)
                print(clientHasPieces)
            elif (messageID == 6):  # REQUEST
                index = ord(sock.recv(4))   # should be equal to (messageLengthInt - 1) / 3
                begin = ord(sock.recv(4))
                block = ord(sock.recv(4))
                print('Index: ' + str(index))
                print('Begin: ' + str(begin))
                print('Block: ' + str(block))
            elif (messageID == 7):  # PIECE
                index = ord(sock.recv(4))
                begin = ord(sock.recv(4))
                block = ord(sock.recv(messageLengthInt - 9))
                print('Index: ' + str(index))
                print('Begin: ' + str(begin))
                print('Block: ' + str(block))
            elif (messageID == 8):  # CANCEL
                index = ord(sock.recv(4))   # should be equal to (messageLengthInt - 1) / 3
                begin = ord(sock.recv(4))
                block = ord(sock.recv(4))
                print('Index: ' + str(index))
                print('Begin: ' + str(begin))
                print('Block: ' + str(block))
            elif (messageID == 9):  # PORT
                listenPort = sock.recv(2)
                print('Listen Port: ' + listenPort)
    
    sock.close

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

def get_peer_IP_list(hexPeerList):
    peerIPs = []
    ip = ''
    currentByte = 0
    for char in hexPeerList:
        if (currentByte < 4):
            if (currentByte == 0):
                ip = str(ord(char))
            else:
                ip += '.' + str(ord(char))
            currentByte += 1
        elif (currentByte == 4):
            peerIPs.append(ip)
            currentByte = 5
        else:
            currentByte = 0
    return peerIPs

def get_peer_port_list(hexPeerList):
    peerPorts = []
    portNumber = 0
    currentByte = 0
    for char in hexPeerList:
        if (currentByte > 3):
            if (currentByte == 4):
                portNumber = ord(char)*256
                currentByte = 5
            else:
                portNumber += ord(char)
                peerPorts.append(portNumber)
                currentByte = 0
        else:
            currentByte += 1
            
    return peerPorts

client()
