from bencode import *
from struct import *
#from socket import *
import hashlib
import socket
import requests
import os
import sys
import msvcrt
import threading

keepAlive = True
isChocked = False
isInterested = False
blockTotalSize = 0
# 2D array of list
peerHasPieces = []

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



#class Client(threading.Thread):
##def __init__(self):
##    threading.Thread.__init__(self)
##def run(self):
def client():
    running = 1
    keyPressed = False
    #filename = 'C:\Users\Xialin\Documents\CS 3251\Let-it-go-frozen.gif.torrent'                           # USE THIS TO TEST BASIC TORRENT FUNCTIONALITY
    filename = 'E:\Downloads\BitTorrentClient\Anathema -- Vol18 [mininova].torrent'                # USE THIS TO TEST MULTIFILE TORRENT
    #filename = 'E:\Downloads\BitTorrentClient\dsl-4.4.10.iso.torrent'                              # USE THIS TO TEST PEERS THAT DO NOT HAVE WHOLE FILE
    #filename = 'E:\Downloads\BitTorrentClient\debian-live-6.0.7-amd64-gnome-desktop.iso.torrent'   # USE THIS TO TEST LARGE FILE TORRENT WITH ENGRYPTION (I THINK)
    bencodeMetaInfo = get_torrent_info(filename)
    #print(bencodeMetaInfo)
    announceKey = get_announce(bencodeMetaInfo)
    #print(announceKey)
    sizeOfFiles = get_length(bencodeMetaInfo)
    #print(sizeOfFiles)
    isMultiFile = False
    if (sizeOfFiles[0] > 1):
        isMultiFile = True
    if (isMultiFile):
        length = sizeOfFiles[sizeOfFiles[0] + 1]
    else:
        length = sizeOfFiles[sizeOfFiles[0]]
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
    #print(sha1HashedInfo)
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
    lengthOfPiecesLeftCopy = lengthOfPiecesLeft
    
    # Actual connections begin here.

    # Handshake
    
    handshakeMessage = pack('>b19s8s20s20s', 19, 'BitTorrent protocol', '', sha1HashedInfo, peerID)
    #print(handshakeMessage)

    numPeers = len(peerIPs)
    noPiecesList = []
    piecesList = []
    for x in range(0, numberOfPieces):
        piecesList.append(False)
        noPiecesList.append(False)

    for x in range(0, numPeers):
        print('Trying peer: ' + str(x))
        if(msvcrt.kbhit()):
            # we will serialize
            while(1):
                if(msvcrt.getch()=='r'):
                    break
                print('Press "r" to resume')
            # try:

            #     #try getting next thing
            # except socket.error, (value, message):
            #     #close socket and try to remkae
            #     if peerSock:
            #         peerSock.close()
        try:
            peerSock = socket.socket()
            host = peerIPs[x]
            port = peerPorts[x]
            peerSock.connect((host, port))
            peerSock.send(handshakeMessage)
            handshakeResponse = peerSock.recv(len(handshakeMessage))
            messageLengthStr = peerSock.recv(4)
            messageLengthInt = parse_message_length(messageLengthStr)
            payload = parse_message(messageLengthInt, peerSock, numberOfPieces)
            if (payload[0] == 5):
                for x in range(numberOfPieces):
                    piecesList[x] = payload[1][x]
                peerHasPieces.append(piecesList)
            peerSock.close()
        except socket.error, (value, message):
            if peerSock:
                peerSock.close()
            peerHasPieces.append(noPiecesList)

    print('Peer Pieces: ' + str(peerHasPieces))

    sock = socket.socket()
    host = peerIPs[1]
    port = peerPorts[1]
    #host = "127.0.0.1"
    #port = 52276
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
    currentFile = 1
    sizeDownloaded = 0
    piece = ''
    fileLocInPiece = [0]
    numFilesInPiece = 0

    if (isMultiFile):
        f = open(infoDict['files'][currentFile-1]['path'][0], 'wb')
        f.close()
    else:
        f = open(infoDict['name'], 'wb')
        f.close()
    #f.close()

    # Message Requesting
    
    while length > 0:
        if(msvcrt.kbhit()):
            while(1):
                if(msvcrt.getch()=='r'):
                    break
                print('Press "r" to resume')
        try:
            if ((lengthOfPiecesLeft[index] - blockSize) > 0):# and (sizeOfFiles[currentFile] - blockSize) > 0):
                # Get piece of size 16384
                requestMessage = pack('>IBIII', 13, 6, index, begin, blockSize) 
                #print('Message Sent: ' + ':'.join(x.encode('hex') for x in requestMessage))

                sock.send(requestMessage)
                messageLengthStr = sock.recv(4)
                messageLengthInt = parse_message_length(messageLengthStr)
                
                payload = parse_message(messageLengthInt, sock, numberOfPieces)

                # If the proper message, do some housekeeping
                if (payload[0] == 7):
                    sentSize = blockSize
                    lengthOfPiecesLeft[index] -= len(payload[3])
                    #length -= len(payload[3])
                    sizeOfFiles[currentFile] -= len(payload[3])
                    begin += sentSize
                    #sizeDownloaded += len(payload[3])
                    if (isMultiFile):
                        f = open(infoDict['files'][currentFile-1]['path'][0], 'ab')
                    else:
                        f = open(infoDict['name'], 'ab')

                    piece += str(payload[3])
                    #write_to_file(f, str(payload[3]))
                    f.close()
                    

                print('Number of Pieces: ' + str(index+1) + '/' + str(numberOfPieces))

            else:
                print('ELSE!!')
                # Get a block of size equal to the rest of the piece.
                sentSize = lengthOfPiecesLeft[index]
                requestMessage = pack('>IBIII', 13, 6, index, begin, sentSize) 
                #print(':'.join(x.encode('hex') for x in requestMessage))

                sock.send(requestMessage)
                messageLengthStr = sock.recv(4)
                messageLengthInt = parse_message_length(messageLengthStr)
                
                payload = parse_message(messageLengthInt, sock, numberOfPieces)

                # Housekeeping
                if (payload[0] == 7):
                    print('Number of Pieces: ' + str(index+1) + '/' + str(numberOfPieces))
                    #sizeOfFiles[currentFile] -= len(payload[3])
                    
                    
                    if (isMultiFile):
                        f = open(infoDict['files'][currentFile-1]['path'][0], 'ab')
                    else:
                        f = open(infoDict['name'], 'ab')

                    piece += str(payload[3])
                    verification = verify_piece(piece, infoDict, index)

                    if (verification):
                        # Write piece to file
                        write_to_file(f, piece)
                        
                        sizeDownloaded += len(piece)
                        length -= len(piece)
                        
                        # move to the next piece
                        index += 1
                        # reset to the start of the piece.
                        begin = 0
                        piece = ''
                    else:
                        lengthOfPiecesLeft = lengthOfPiecesLeftCopy[index]
                        # Discard piece, start over
                    f.close()
                    
                
            
            if (index >= numberOfPieces):
                index -= 1
            #print('Length of Current File: ' +  str(sizeOfFiles[currentFile]))
            print('Length Remaining: ' + str(length))
            print('Length of Piece Remaining: ' + str((lengthOfPiecesLeft[index])))
            print('Sized Downloaded So Far: ' + str(sizeDownloaded))

            #try getting next thing
        except socket.error, (value, message):
            #close socket and try to remkae
            if sock:
                sock.close()
            sock.connect((host, port))
            sock.send(handshakeMessage)
            handshakeResponse = sock.recv(len(handshakeMessage))
            print('Handshake Message: ' + handshakeMessage)
            print('Handshake Response: ' + handshakeResponse)
    print('Total block size: ' + str(blockTotalSize))
    f.close()
    sock.close
    running = 0

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
    global blockTotalSize
    clientHasPieces = []

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
            #block = bytearray(messageLengthInt - 9)
            block = ''
            sizeReceived = 0
            currIndex = 1
            #f = open('TEST.pdf', 'w')
            while sizeReceived < (messageLengthInt - 9):
                segment = sock.recv(messageLengthInt - 9 - sizeReceived)
                #print('SEGMENT ' + str(currIndex) + ': ' + segment)
                #block[currIndex:len(segment)] = segment
                block += segment
                currIndex += 1
                #f.write(segment)
                sizeReceived += len(segment)
            

            blockTotalSize += len(block)
            print('Index: ' + str(index))
            print('Begin: ' + str(begin))
            print('Block Size: ' + str(len(block)))
            #print('BlockByte: ' + block)
            #f.close()
            #print('BlockStr: ' + str(block))
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

def verify_piece(piece, infoDict, currentPiece):
    piecesDecoded = infoDict['pieces']
    hashedPiece = piecesDecoded[currentPiece*20:currentPiece*20 + 20]
    print('given: ')
    print(hashedPiece)
    
    print('taken: ')
    print(hashlib.sha1(piece).digest())
    if (hashlib.sha1(piece).digest() == hashedPiece):
        return True
    else:
        return False

def listen_for_new_peer():
    print('Listening for peer!')
    filename = 'E:\Downloads\BitTorrentClient\Anathema -- Vol18 [mininova].torrent'                # USE THIS TO TEST MULTIFILE TORRENT
    bencodeMetaInfo = get_torrent_info(filename)
    infoDict = get_info(bencodeMetaInfo)
    encodedInfo = bencode_info(infoDict)
    sha1HashedInfo = hashlib.sha1(encodedInfo).digest()
    
    host = '128.61.89.77' 
    port = 57894 
    s = socket() 
    s.bind((host,port)) 
    s.listen(1)
    handshakeMessage = pack('>B19s8s20s20s', 19, 'BitTorrent protocol', '', sha1HashedInfo, 'iamlisteningtoyou!!')
    print(handshakeMessage)
    notFound = True
    while notFound: 
        client, address = s.accept() 
        data = client.recv(4096)
        print(data)
        if (data[28:48] == sha1HashedInfo):
            print(data[28:48])
            print(sha1HashedInfo)
            print('yay! I heard you!')
            notFound = False
                  
        client.close()

#listen_for_new_peer()
client()
