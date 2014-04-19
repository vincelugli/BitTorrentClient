from bencode import *
from struct import *
import hashlib
import requests
import socket

keepAlive = True
isChocked = False
isInterested = False
clientHasPieces = []

options = {0 : 'choke',
           1 : 'unchoke',
           2 : 'interested',
           3 : 'not interested',
           4 : 'have',
           5 : 'bitfield',
           6 : 'request',
           7 : 'piece',
           8 : 'cancel',
           9 : 'port',
           10 : 'keep-alive', }

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
    numberOfPieces = get_number_of_pieces(infoDict)
    #print(numberOfPieces)
    lengthOfPiece = get_length_of_piece(infoDict)
    print(lengthOfPiece)
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

    # List for the length of each piece remaining to be downloaded
    
    lengthOfPiecesLeft = []
    blockSize = 16384     # 2^14 bytes
    lengthLeft = length
    while lengthLeft > 0:
        if (lengthLeft - lengthOfPiece >= 0):
            lengthOfPiecesLeft.append(lengthOfPiece)
        else:
            lengthOfPiecesLeft.append(lengthLeft)
        lengthLeft -= lengthOfPiece
    print(lengthOfPiecesLeft)

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

    # Cases for message: keep-alive, choke, unchoke, interested, not-interested, have, bitfield, request, piece, cancel, and port
    
    messageLengthStr = sock.recv(4)
    print(unpack('>4B', messageLengthStr))
    messageLengthInt = parse_message_length(messageLengthStr)
    
    payload = parse_message(messageLengthInt, sock, numberOfPieces)
    print(payload)
    
    messageLengthStr = sock.recv(4)
    messageLengthInt = parse_message_length(messageLengthStr)
    
    payload = parse_message(messageLengthInt, sock, numberOfPieces)
    print(payload)

    # Send an interested message to get to download files
    requestMessage = pack('ib', 1, 2)
    sock.send(requestMessage)
    
    messageLengthStr = sock.recv(4)
    messageLengthInt = parse_message_length(messageLengthStr)
    
    payload = parse_message(messageLengthInt, sock, numberOfPieces)
    print(payload)

    index = 0
    begin = 0
    sentSize = 0
    #f = open('test.txt', 'w')
    #f.write('Testing!')

    # Message Requesting
    # TODO: change endianness from little to big
    
    while length > 0:
        if ((lengthOfPiecesLeft[index] - blockSize) > 0):
            begin += blockSize
            requestMessage = pack('>ibiii', 13, 6, index, begin, blockSize)
            sentSize = blockSize
        else:
            sentSize = lengthOfPiecesLeft[index]
            requestMessage = pack('>ibiii', 13, 6, index, begin, sentSize)
            index += 1
        length -= sentSize
        
        sock.send(requestMessage)
        messageLengthStr = sock.recv(4)
        messageLengthInt = parse_message_length(messageLengthStr)
        
        payload = parse_message(messageLengthInt, sock, numberOfPieces)
        print(payload)

        #received = sock.recv(sentSize)
        #print(received)     # This should be a PIECE message. Currently, it's not...
        #write_to_file(f, received)
    
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

def get_number_of_pieces(infoDict):
    return len(infoDict['pieces']) / 20

def get_length_of_piece(infoDict):
    return infoDict['piece length']

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

def parse_message_length(messageLengthStr):
    messageLengthInt = 0
    for x in range(0, len(messageLengthStr)):
        messageLengthInt += (10**(4-x))*ord(messageLengthStr[x])

    return messageLengthInt

def parse_message(messageLengthInt, sock, numberOfPieces):
    # Global declarations
    global keepAlive
    global isChocked
    global isInterested
    global clientHasPieces

    print('---------------')
    
    if (messageLengthInt != 0):
        messageID = ord(sock.recv(1))
    else:
        messageID = 10
    print('Message: ' + options[messageID])
    if (messageLengthInt == 0):         # KEEP-ALIVE
        keepAlive = True
    elif (messageID == 0):              # CHOKE
        isChocked = True
    elif (messageID == 1):              # UNCHOKE
        isChocked = False
    elif (messageID == 2):              # INTERESTED
        isInterested = True
    elif (messageID == 3):              # UNINTERESTED
        isInterested = False
    else:
        if (messageID == 4):            # HAVE
            content = sock.recv(messageLengthInt-1)
            # not sure what to do with the piece index here...
            print('Piece Index: ' + content)
            return [messageID, content]
        elif (messageID == 5):          # BITFIELD
            bitfield = bin(ord(sock.recv(messageLengthInt-1)))
            print('BitField: ' + bitfield)
            # Looking to see which pieces the client has.
            for x in range(2, numberOfPieces+2):
                if (bitfield[x] == '1'):
                    clientHasPieces.append(True)
                else:
                    clientHasPieces.append(False)
            print(clientHasPieces)
            return [messageID, clientHasPieces]
        elif (messageID == 6):          # REQUEST
            index = ord(sock.recv(4))   # should be equal to (messageLengthInt - 1) / 3
            begin = ord(sock.recv(4))
            block = ord(sock.recv(4))
            print('Index: ' + str(index))
            print('Begin: ' + str(begin))
            print('Block: ' + str(block))
            return [messageID, index, begin, block]
        elif (messageID == 7):          # PIECE
            index = ord(sock.recv(4))
            begin = ord(sock.recv(4))
            block = ord(sock.recv(messageLengthInt - 9))
            print('Index: ' + str(index))
            print('Begin: ' + str(begin))
            print('Block: ' + str(block))
            return [messageID, index, begin, block]
        elif (messageID == 8):          # CANCEL
            index = ord(sock.recv(4))   # should be equal to (messageLengthInt - 1) / 3
            begin = ord(sock.recv(4))
            block = ord(sock.recv(4))
            print('Index: ' + str(index))
            print('Begin: ' + str(begin))
            print('Block: ' + str(block))
            return [messageID, index, begin, block]
        elif (messageID == 9):          # PORT
            listenPort = sock.recv(2)
            print('Listen Port: ' + listenPort)
            return [messageID, listenPort]

def write_to_file(f, content):
    f.write(content)

client()
