use zmq::Context;
use uuid::Uuid;

// === ZMQ COMMUNICATION ===

//NOTE: Rust is pretty strict about thread saftey so we wrap the zmq socket
// (which is all we need persistant access to since it stores an arc ref to ctx), within a static mutex so we can safely access it everywhere.
// EG.
// lazy_static! {
//     static ref SERVE_SOX: Mutex<SocketHandle> = Mutex::new(SocketHandle::new(
//         SocketType::PUB,
//         "tcp://127.0.0.1:9876",
//         "data"
//     ));
// }

#[derive(PartialEq)]
pub enum SocketType {
    SUB,
    PUB,
    DEALER,
}

/// Wrapper around the zmq socket.
/// Used so we can initlize a socket once and then use it everywhere, within a mutex.  
pub struct SocketHandle {
    sox: zmq::Socket,
    socket_type: SocketType,
    topic: String,
}

impl SocketHandle {
    /// Create a new socket handle. Address and topic fields used for both PUB and SUB.
    /// Bound topic is used for password in a dealer...
    pub fn new(socket_type: SocketType, bound_address: &str, bound_topic: &str) -> Result<Self, std::io::Error> {
        let context = Context::new();
        match socket_type{
            SocketType::SUB => {
            let socket = context.socket(zmq::SUB).unwrap();
            match socket.connect(bound_address) {
                Ok(_) => println!("SUBSCRIBER Bound to tcp"),
                Err(_) => println!("SUBSCRIBER Failed to bind to tcp"),
            };
            match socket.set_subscribe(bound_topic.as_bytes()) {
                Ok(_) => println!("Subscribed to {}", bound_topic),
                Err(_) => println!("Failed to subscribe to {}", bound_topic),
            };
            return Ok(Self {
                sox: socket,
                socket_type: socket_type,
                topic: String::from(bound_topic),
            });
        }
        SocketType::PUB => 
        {
            let socket = context.socket(zmq::PUB).unwrap();
            match socket.bind(bound_address) {
                Ok(_) => println!("PUBLISHER Bound to tcp"),
                Err(_) => println!("PUBLISHER Failed to bind to tcp"),
            };
            return Ok(Self {
                sox: socket,
                socket_type: socket_type,
                topic: String::from(bound_topic),
            });
        }
        SocketType::DEALER =>{
            let socket = context.socket(zmq::DEALER).unwrap();
            socket.set_plain_username(Some("rcon"))?;
            socket.set_plain_password(Some(bound_topic))?;
            socket.set_zap_domain("rcon")?;
            socket.set_identity(&Uuid::new_v4().to_bytes_le())?;//set uuid here
            
            match socket.connect(bound_address){
                Ok(_) => {println!("DEALER Bound to tcp");
                        //If bound okay register with the server
                        socket.send("register".as_bytes(), 0)?;}
                Err(_) => println!("DEALER Failed to bind to tcp"),
            };
            return Ok(Self {
                sox: socket,
                socket_type: socket_type,
                topic: String::from(bound_topic),
            });
        }
    }
}
    /// Receive a message from the socket. returns a string.  User turns it into json or whatever.
    pub fn recv(&self) -> Option<String> {
        match self.socket_type {
            SocketType::SUB => {
                let mut msg = zmq::Message::new();
                let mut _recv: Result<(), zmq::Error> = match self.sox.recv(&mut msg, zmq::DONTWAIT) {
                    Ok(c) => Ok(c),
                    Err(_) => return None,
                };
                let mut output = String::new();
                output.push_str(msg.as_str().unwrap());
                return Some(output);
            }
            SocketType::PUB => {
                panic!("Cannot receive on a PUB socket. Use a SUB socket to receive messages.")
            }
            SocketType::DEALER => {
                let mut msg = zmq::Message::new();
                let mut _recv: Result<(), zmq::Error> = match self.sox.recv(&mut msg, zmq::DONTWAIT) {
                    Ok(c) => Ok(c),
                    Err(_) => return None,
                };
                let mut output = String::new();
                if msg.as_str().is_none() {
                    return None;
                }
                output.push_str(msg.as_str().unwrap());
                return Some(output);
            }
        }
    }
    /// Send a message on the socket.
    pub fn send(&self, message: String) {
        match self.socket_type {
            SocketType::SUB => {
                panic!("Cannot send on a SUB socket. Use a PUB socket to send messages.")
            }
            SocketType::DEALER => {
                let msg = zmq::Message::from(message.as_bytes());
    
                match self.sox.send(msg, 0) {
                    Ok(_) => {} 
                    Err(_) => println!("Failed to send: {:?}", message),
                }
            }
            SocketType::PUB => {}
        }
    }
}