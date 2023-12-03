
use tokio::sync::Mutex;
use crate::zmq_comm::SocketHandle;

pub struct Data {pub mappool: Mutex<Vec<String>>, pub zmq_send_handle: Mutex<SocketHandle> } // User data, which is stored and accessible in all command invocations
pub type Error = Box<dyn std::error::Error + Send + Sync>;
pub type Context<'a> = poise::Context<'a, Data, Error>;