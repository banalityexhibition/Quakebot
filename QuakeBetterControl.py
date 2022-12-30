#!/usr/bin/env python

import sys
import time
import struct
import argparse
import uuid
import threading
import queue

import discord
import time
import logging
logging.basicConfig( format='%(message)s', level=logging.DEBUG )

import zmq

import unittest

##==== Declare some static strings ====##
helpstring = """ 
***I'M DA OAT BOT BABY*** \n
`★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★`\n
__**Direct Server Interaction**__\n
**>** : *Input Command* - Prefixes server side commands 
**<** : *Pipe Command* - Returns server output, slow, probably don't use this \n
__**Macros**__\n
**!help**: *Help* - looking at it bitch 
**!connect**: *Connect* - Runs registration with the server, this is done after our first command anyways but this prevents it from being lost...
**!mpupdate** : *Update Pools* - Checks current mappool files on server 
**!mplist** : *List Pools* - Marco to see current map pools on server 
**!mpcurrent** : *List Current Mappool* - Shows current map pool 
**!mp** : *Map Pool* - Macro to change map pools without multi command, starts random map after load, will auto prepend mappool_ and append .txt and for you \n
`★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★`

"""

currentmappool = "XXX"
intents = discord.Intents.default()
intents.messages = True
client = discord.Client(intents=intents)
fistconnect = 0



def _readSocketEvent( msg ):
    # NOTE: little endian - hopefully that's not platform specific?
    event_id = struct.unpack( '<H', msg[:2] )[0]
    # NOTE: is it possible I would get a bitfield?
    event_names = {
        zmq.EVENT_ACCEPTED : 'EVENT_ACCEPTED',
        zmq.EVENT_ACCEPT_FAILED : 'EVENT_ACCEPT_FAILED',
        zmq.EVENT_BIND_FAILED : 'EVENT_BIND_FAILED',
        zmq.EVENT_CLOSED : 'EVENT_CLOSED',
        zmq.EVENT_CLOSE_FAILED : 'EVENT_CLOSE_FAILED',
        zmq.EVENT_CONNECTED : 'EVENT_CONNECTED',
        zmq.EVENT_CONNECT_DELAYED : 'EVENT_CONNECT_DELAYED',
        zmq.EVENT_CONNECT_RETRIED : 'EVENT_CONNECT_RETRIED',
        zmq.EVENT_DISCONNECTED : 'EVENT_DISCONNECTED',
        zmq.EVENT_LISTENING : 'EVENT_LISTENING',
        zmq.EVENT_MONITOR_STOPPED : 'EVENT_MONITOR_STOPPED',
    }
    event_name = event_names[ event_id ] if event_id in event_names else '%d' % event_id
    event_value = struct.unpack( '<I', msg[2:] )[0]
    return ( event_id, event_name, event_value )

def _checkMonitor( monitor ):
    try:
        event_monitor = monitor.recv( zmq.NOBLOCK )
    except zmq.Again:
        #logging.debug( 'again' )
        return

    ( event_id, event_name, event_value ) = _readSocketEvent( event_monitor )
    event_monitor_endpoint = monitor.recv( zmq.NOBLOCK )
    logging.info( 'monitor: %s %d endpoint %s' % ( event_name, event_value, event_monitor_endpoint ) )
    return ( event_id, event_value )


def pred(m):
    return True
    #logging.info( 'zmq python bindings %s, libzmq version %s' % ( repr( zmq.__version__ ), zmq.zmq_version() ) )
parser = argparse.ArgumentParser( description = 'Verbose QuakeLive server statistics' )
parser.add_argument( '--host', default = "", help = 'ZMQ URI to connect to. Defaults to %s' % "111" )
    #parser.add_argument( '--password', required = False )
    #parser.add_argument( '--identity', default = uuid.uuid1().hex, help = 'Specify the socket identity. Random UUID used by default' )
args = parser.parse_args()

mappools = ""

try:
    POLL_TIMEOUT = 1000
    ctx = zmq.Context()
    socket = ctx.socket( zmq.DEALER )
    monitor = socket.get_monitor_socket( zmq.EVENT_ALL )
   
    logging.info( 'setting password for access' )
    socket.plain_username = b'rcon'
    socket.plain_password = b''
    socket.zap_domain = b'rcon'
    socket.setsockopt_string( zmq.IDENTITY, uuid.uuid1().hex )
    #socket.setsockopt(zmq.RCVHWM, 5)
    #socket.setsockopt(zmq.CONFLATE, 1) Not used.. just run mpupdate early on lol
    socket.connect(args.host)
    print( 'Connecting to ' + args.host )
   


except Exception as e:
    print("ass")
    logging.info( e ) 



@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    event = socket.poll( POLL_TIMEOUT )
    event_monitor = _checkMonitor( monitor )
    if ( event_monitor is not None and event_monitor[0] == zmq.EVENT_CONNECTED ):
     # application layer protocol - notify the server of our presence
        logging.info( 'Registering with the server.' )
        socket.send( b'register' )
        

                


@client.event
async def on_message(message):
    global mappools
    global currentmappool
    if message.author == client.user:
        return
    print("\n ***")
    print(message.content)
    print(message.author)
    print("\n ***")
    if message.content.startswith('>'):
        messoge = bytearray(message.content, "utf-8")
        socket.send(messoge[1:])
        await message.channel.send(" `Exec: " + messoge.decode("utf-8") + "`")
    elif message.content.startswith('<'):
        messoge = bytearray(message.content, "utf-8")
        socket.send(messoge[1:])
        await message.channel.send("`Exec PipeCommand : " + messoge.decode("utf-8") + "`")
        while ( True ):
            try:
                msg = socket.recv( zmq.NOBLOCK )
            except zmq.error.Again:
                break
            except Exception as e:
                print("recieve excpetion error")
                logging.info( e )
                break
            else:

                await message.channel.send(msg.decode("utf-8") )
    elif message.content.startswith('!help'):
        await message.channel.send(helpstring)
    elif message.content.startswith('!mplist'):
        await message.channel.send("```" + mappools + "```")
    elif message.content.startswith("!mpupdate"):
        mappools = "MapPools: \n \n"
        socket.send( b'fdir /mappool*' )
        while ( True ):
            try:
                msg = socket.recv()
            except zmq.error.Again:
                print("Cleared Messge Queue")
                break
            except Exception as e:
                print("recieve excpetion error")
                logging.info( e )
                break
            
                
            if ".txt" in msg.decode("utf-8"):
                mappools += msg.decode("utf-8")[1:] + "\n"
            elif "listed" in msg.decode("utf-8"):
                await message.channel.send("`pool updated...`")
                break
    elif message.content.startswith("!connect"):
        messoge = bytearray("echo I am online!", "utf-8")
        i = 0
        socket.send(messoge)
        global fistconnect
        if fistconnect == 0:
            await message.channel.send(" ``` First connection from me! \n I'm probably online, QuakeZMQ doesn't give a response on fist connect. \n If you're a paranoid freak run this again to make sure, I'll tell you if I get a response from the server... ```")
            fistconnect = 1
        else:
            await message.channel.send(" ` I am online! (probably.. This isnt a great check lol) `")


    elif message.content.startswith("!mpcurrent"):
        await message.channel.send("`Current Mappool is:" + currentmappool + "`")

    elif message.content.startswith("!mp"):
        if ".txt" in mappools:
            messoge =  bytearray(message.content, "utf-8")
            currentmappool = message.content[3:]
            if ".txt" not in message.content and "mappool" not in message.content:
                socket.send(b'set sv_mappoolfile mappool_' + messoge[4:] + b'.txt')
            elif "mappool_" in message.content and ".txt" not in message.content:
                socket.send(b'set sv_mappoolfile ' + messoge[3:]+ b'.txt')
            else:
                socket.send(b'set sv_mappoolfile '+ messoge[3:])
            time.sleep(0.5)
            socket.send(b'reload_mappool')
            time.sleep(0.5)
            socket.send(b'startrandommap')
            await message.channel.send("`Mappool set to:" + message.content[3:] + "`")
        else:
            await message.channel.send(" ` Run !mpupdate to update map pool file first... `")
    


client.run('TOKEN')






# bunch of experiments that didn't go in the riht direction
class Test( unittest.TestCase ):
    def testPair( self ):
        timeline = time.time()
        
        HOST = 'tcp://127.0.0.1:27960'
        POLL_TIMEOUT = 1000
        
        server_ctx = zmq.Context()
        server_socket = server_ctx.socket( zmq.PAIR )

        monitor = server_socket.get_monitor_socket( zmq.EVENT_ALL )
        
        server_socket.bind( HOST )

        client_ctx_1 = zmq.Context()
        client_socket_1 = client_ctx_1.socket( zmq.PAIR )
        client_socket_1.connect( HOST )

        client_ctx_2 = zmq.Context()
        client_socket_2 = client_ctx_2.socket( zmq.PAIR )
        client_socket_2.connect( HOST )

        while ( True ):
            event = server_socket.poll( POLL_TIMEOUT )
            _checkMonitor( monitor )
            if ( time.time() - timeline > 4 ):
                break

        timeline = time.time()
        
        server_socket.send( 'console line 1' )
        server_socket.send( 'console line 2' )

        ev1 = client_socket_1.poll( POLL_TIMEOUT )
        ev2 = client_socket_2.poll( POLL_TIMEOUT )

        # won't sustain multiple peers ..
        logging.info( repr( [ ev1, ev2 ] ) )
        self.assertEqual( [ ev1, ev2 ], [ 1, 0 ] )

    def testMix( self ):
        HOST = 'tcp://127.0.0.1:27960'
        POLL_TIMEOUT = 1000
        
        server_ctx = zmq.Context()
        
        server_pub = server_ctx.socket( zmq.PUB )
        server_pub.bind( HOST )
        monitor_pub = server_pub.get_monitor_socket( zmq.EVENT_ALL )

        # yeah you can't
        server_rep = server_ctx.socket( zmq.REP )
        self.assertRaises( zmq.ZMQError, server_rep.bind, HOST )

    def testMulti( self ):
        timeline = time.time()
        
        HOST = 'tcp://127.0.0.1:27960'
        POLL_TIMEOUT = 1000
        
        server_ctx = zmq.Context()

        server_rep = server_ctx.socket( zmq.REP )
        server_rep.bind( HOST )
        monitor = server_rep.get_monitor_socket( zmq.EVENT_ALL )

        client_ctx_1 = zmq.Context()
        client_socket_1 = client_ctx_1.socket( zmq.REQ )
        client_socket_1.connect( HOST )

        client_ctx_2 = zmq.Context()
        client_socket_2 = client_ctx_2.socket( zmq.REQ )
        client_socket_2.connect( HOST )

        client_socket_1.send( 'req 1' )
        client_socket_2.send( 'req 2' )
        
        while ( True ):
            event = server_rep.poll( POLL_TIMEOUT )
            _checkMonitor( monitor )

            if ( time.time() - timeline > 4 ):
                break
            
            if ( event == 0 ):
                continue

            msg = server_rep.recv( zmq.NOBLOCK )
            logging.info( repr( msg ) )
            server_rep.send( 'ack' ) # REQ/REP always have to ack

# summarizes a working setup and details QL's implementation
# based on http://zguide2.zeromq.org/py%3aall#Asynchronous-Client-Server
class TestRcon( unittest.TestCase ):
    def test( self ):
        timeline = time.time()
        
        HOST = 'tcp://127.0.0.1:27960'
        POLL_TIMEOUT = 1000
        
        server_ctx = zmq.Context()
        server = server_ctx.socket( zmq.ROUTER )
        server.bind( HOST )

        client_ctx_1 = zmq.Context()
        client_socket_1 = client_ctx_1.socket( zmq.DEALER )
        client_socket_1.setsockopt_string( zmq.IDENTITY, 'client-1' )
        client_socket_1.connect( HOST )
        client_socket_1.send( 'hello' ) # first message is ignored and used to notify server of presence
        client_socket_1.send( 'do this' )

        client_ctx_2 = zmq.Context()
        client_socket_2 = client_ctx_2.socket( zmq.DEALER )
        client_socket_2.setsockopt_string( zmq.IDENTITY, 'client-2' )
        client_socket_2.connect( HOST )
        client_socket_2.send( 'hello' )
        client_socket_2.send( 'do that' )

        clients = []
        
        while ( True ):
            event = server.poll( POLL_TIMEOUT )
            if ( event == 0 ):

                if ( time.time() - timeline > 2 ):
                    # console output would blindly go to all connected clients
                    for id in clients:
                        server.send( id, zmq.SNDMORE )
                        server.send( 'console line 1' )
                    break
                
                continue

            client_id = server.recv()
            msg = server.recv()

            try:
                clients.index( client_id )
            except:
                logging.info( 'new client %s' % client_id )
                clients.append( client_id )
                continue

            logging.info( 'client %s sends command %s' % ( client_id, repr( msg ) ) )

        # read the console lines

        def pollClient( id, client ):
            event = client.poll( POLL_TIMEOUT )
            if ( event == 0 ):
                return

            msg = client.recv()
            logging.info( 'client %s: %s' % ( id, msg ) )

        pollClient( 'client-1', client_socket_1 )
        pollClient( 'client-2', client_socket_2 )

        # client 1 disconnects
        client_socket_1.close()

        monitor = server.get_monitor_socket( zmq.EVENT_ALL )
        
        server.send( 'client-1', zmq.SNDMORE )
        server.send( 'console line 2' )

        time.sleep( 1 )

        # we get EVENT_DISCONNECTED - and the endpoint in metadata
        # the server matches this to know which client is disconnected
        _checkMonitor( monitor )

# start a thread, read a queue that will read input lines
def setupInputQueue():
    def waitStdin( q ):
        while ( True ):
            l = sys.stdin.readline()
            q.put( l )
    q = queue.Queue()
    t = threading.Thread( target = waitStdin, args = ( q, ) )
    t.daemon = True
    t.start()
    return q

class TestInput( unittest.TestCase ):
    @unittest.skip("requires interaction")
    def test( self ):
        while ( True ):
            logging.info( 'waiting on readline' )
            line = sys.stdin.readline()
            logging.info( 'input: %s' % repr( line ) )

    @unittest.skip("requires interaction")
    def testBGRead( self ):
        q = setupInputQueue()
        while ( True ):
            logging.info( 'sleep' )
            time.sleep( 0.5 )
            while ( not q.empty() ):
                l = q.get()
                logging.info( 'input: %s' % repr( l ) )

HOST = 'tcp://127.0.0.1:27961'
POLL_TIMEOUT = 100

def WriteMessageFormatted( inbytes ):
    # Skip empty messages
    message = inbytes.decode("utf-8")
    if len( message ) == 0:
        return
    
    # Strip unnecessary chars
    message = message.replace( "\n", "" )
    message = message.replace( "\\n", "", )
    message = message.replace( chr(25), "" )

    # Use mIRC color codes
    message = message.replace( "^0", chr(3) + "0,01" )  # black
    message = message.replace( "^1", chr(3) + "4,01" )  # red
    message = message.replace( "^2", chr(3) + "9,01" )  # green
    message = message.replace( "^3", chr(3) + "8,01" )  # yellow
    message = message.replace( "^4", chr(3) + "12,01" ) # blue
    message = message.replace( "^5", chr(3) + "11,01" ) # cyan
    message = message.replace( "^6", chr(3) + "13,01" ) # magenta
    message = message.replace( "^7", chr(3) + "0,01" )  # white

    # Strip broadcast statement
    if message[:10] == "broadcast:":
        message = message[11:]

    # Strip print statement
    if message[:7] == "print \"":
        message = message[7:-1]
    # Write
    logging.info( message )  


