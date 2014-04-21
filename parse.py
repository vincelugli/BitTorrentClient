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
    filename = 'E:\Downloads\BitTorrentClient\The Chris Gethard Show - Episode-.torrent'                            # USE THIS TO TEST BASIC TORRENT FUNCTIONALITY
    #filename = 'E:\Downloads\BitTorrentClient\Anathema -- Vol18 [mininova].torrent'                # USE THIS TO TEST MULTIFILE TORRENT
    #filename = 'E:\Downloads\BitTorrentClient\dsl-4.4.10.iso.torrent'                              # USE THIS TO TEST PEERS THAT DO NOT HAVE WHOLE FILE
    #filename = 'E:\Downloads\BitTorrentClient\debian-live-6.0.7-amd64-gnome-desktop.iso.torrent'   # USE THIS TO TEST LARGE FILE TORRENT WITH ENGRYPTION (I THINK)
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
    #print(lengthOfPiece)
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
    #print(lengthOfPiecesLeft)

    # Actual connections begin here.

    # Handshake
    
    handshakeMessage = pack('>b19s8s20s20s', 19, 'BitTorrent protocol', '', sha1HashedInfo, peerID)
    #print(handshakeMessage)

    sock = socket.socket()
    host = peerIPs[1]
    port = peerPorts[1]
    
    sock.connect((host, port))
    sock.send(handshakeMessage)
    handshakeResponse = sock.recv(len(handshakeMessage))
    print('Handshake Message: ' + handshakeMessage)
    print('Handshake Response: ' + handshakeResponse)
    # Message Passing (keep-alive, choke, unchoke, interested, not-interested, have, etc...)

    # Cases for message: keep-alive, choke, unchoke, interested, not-interested, have, bitfield, request, piece, cancel, and port
    
    messageLengthStr = sock.recv(4)
    #print(':'.join(x.encode('hex') for x in messageLengthStr))
    messageLengthInt = parse_message_length(messageLengthStr)
    
    payload = parse_message(messageLengthInt, sock, numberOfPieces)
    #print(payload)
    
    messageLengthStr = sock.recv(4)
    messageLengthInt = parse_message_length(messageLengthStr)
    
    payload = parse_message(messageLengthInt, sock, numberOfPieces)
    print(payload)

    # Send an interested message to get to download files
    while (payload[0] != 1):
        requestMessage = pack('>ib', 0001, 2)   
        sock.send(requestMessage)
        
        messageLengthStr = sock.recv(4)
        messageLengthInt = parse_message_length(messageLengthStr)
        
        payload = parse_message(messageLengthInt, sock, numberOfPieces)
        print(payload)

    index = 0
    begin = 0
    sentSize = 0
    f = open(infoDict['name'], 'w')# FOR MULTI FILE: infoDict['files'][0]['path'][0], 'w')
    
    # Message Requesting
    # TODO: change endianness from little to big
    
    while length > 0:
        print('Length Remaining: ' + str(length))
        if ((lengthOfPiecesLeft[index] - blockSize) > 0):
            requestMessage = pack('>IBIII', 13, 6, index, begin, blockSize) 
            print('Message Sent: ' + ':'.join(x.encode('hex') for x in requestMessage))

            sock.send(requestMessage)
            messageLengthStr = sock.recv(4)
            messageLengthInt = parse_message_length(messageLengthStr)
            
            payload = parse_message(messageLengthInt, sock, numberOfPieces)
            if (payload[0] == 7):
                sentSize = blockSize
                begin += sentSize
        else:
            print('In Else')
            sentSize = lengthOfPiecesLeft[index]
            requestMessage = pack('>IBIII', 13, 6, index, begin, sentSize) 
            print(':'.join(x.encode('hex') for x in requestMessage))

            sock.send(requestMessage)
            messageLengthStr = sock.recv(4)
            messageLengthInt = parse_message_length(messageLengthStr)
            
            payload = parse_message(messageLengthInt, sock, numberOfPieces)
            if (payload[0] == 7):
                index += 1
                begin = 0
        length -= sentSize
        if (payload[0] == 7):
            write_to_file(f, payload[3])
    
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
        print('MULTIPLE FILES!')
        files = metainfo['info']['files']
        total = 0
        for filePart in files:
            total += filePart['length']
        return total        
    else:
        print('SINGLE FILE!')
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
    print('---------------')
    #print('Length as Str: ' + ':'.join(x.encode('hex') for x in messageLengthStr))
    messageLengthInt = unpack('>I', messageLengthStr)[0]
    #print('Length: ' + str(messageLengthInt))
    return messageLengthInt

def parse_message(messageLengthInt, sock, numberOfPieces):
    # Global declarations
    global keepAlive
    global isChocked
    global isInterested
    global clientHasPieces
    
    if (messageLengthInt != 0):
        messageID = unpack('>B', sock.recv(1))[0]
    else:
        messageID = 10
        print('Message: ' + options[messageID])
        return [messageID, True]
    #print('Message ID: ' + str(messageID))
    if (messageID < 10):
        print('Message: ' + options[messageID])
    else:
        print('Not a valide ID. Message ignored.')
        return [11]
    if (messageLengthInt == 0):         # KEEP-ALIVE
        keepAlive = True
        return [messageID, True]
    elif (messageID == 0):              # CHOKE
        isChocked = True
        return [messageID, True]
    elif (messageID == 1):              # UNCHOKE
        isChocked = False
        return [messageID, False]
    elif (messageID == 2):              # INTERESTED
        isInterested = True
        return [messageID, True]
    elif (messageID == 3):              # UNINTERESTED
        isInterested = False
        return [messageID, False]
    else:
        if (messageID == 4):            # HAVE
            content = sock.recv(messageLengthInt-1)
            # not sure what to do with the piece index here...
            print('Piece Index: ' + content)
            return [messageID, content]
        elif (messageID == 5):          # BITFIELD
            strBitfield = sock.recv(messageLengthInt-1)
            hexBitfield = ''.join(x.encode('hex') for x in strBitfield)
            binBitfield = bin(int(hexBitfield, 16))
            print('BitField: ' + ':'.join(x.encode('hex') for x in strBitfield))
            # Looking to see which pieces the client has.
            for x in range(2, len(binBitfield)):
                if (binBitfield[x] == '1'):
                    clientHasPieces.append(True)
                else:
                    clientHasPieces.append(False)
            print(clientHasPieces)
            return [messageID, clientHasPieces]
        elif (messageID == 6):          # REQUEST
            index = unpack('>I', sock.recv(4))[0]   # should be equal to (messageLengthInt - 1) / 3
            begin = unpack('>I', sock.recv(4))[0]
            length = unpack('>I', sock.recv(4))[0]
            print('Index: ' + str(index))
            print('Begin: ' + str(begin))
            print('Block: ' + str(length))
            return [messageID, index, begin, length]
        elif (messageID == 7):          # PIECE
            index = unpack('>I', sock.recv(4))[0]   # should be equal to (messageLengthInt - 1) / 3
            begin = unpack('>I', sock.recv(4))[0]
            block = ''
            sizeReceived = 0
            while sizeReceived < (messageLengthInt -9):
                block += sock.recv(messageLengthInt - 9 - sizeReceived)
                sizeReceived = len(block)
            
            print('Index: ' + str(index))
            print('Begin: ' + str(begin))
            print('Block: ' + str(len(block)))
            return [messageID, index, begin, block]
        elif (messageID == 8):          # CANCEL
            index = unpack('>I', sock.recv(4))[0]   # should be equal to (messageLengthInt - 1) / 3
            begin = unpack('>I', sock.recv(4))[0]
            length = unpack('>I', sock.recv(4))[0]
            print('Index: ' + str(index))
            print('Begin: ' + str(begin))
            print('Block: ' + str(length))
            return [messageID, index, begin, length]
        elif (messageID == 9):          # PORT
            listenPort = sock.recv(2)
            print('Listen Port: ' + listenPort)
            return [messageID, listenPort]

def write_to_file(f, content):
    f.write(content)

client()
