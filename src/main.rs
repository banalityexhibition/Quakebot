use poise::serenity_prelude as serenity;

mod utils;
mod commands;
mod statics;
mod zmq_comm;
mod serenity_structs;
use serenity_structs::Data;
use tokio::sync::Mutex;
use zmq_comm::SocketHandle;


#[tokio::main]
async fn main() {
    //injest our config data
    let cfg_data = utils::read_config_data("quakebot.config".to_string()).expect("Failed to read config file");
    println!("Discord Token: {}", cfg_data.discord_token);
    println!("Sub to: {}:{}", cfg_data.server_ip, cfg_data.server_port);
    //setup framework
    let framework = poise::Framework::builder()
        .options(poise::FrameworkOptions {
            commands: vec![commands::help(), commands::change_mappool(), commands::list_mappool(), commands::current_mappool(), commands::rcon()],
            ..Default::default()
        })
        .token(cfg_data.discord_token)
        .intents(serenity::GatewayIntents::non_privileged())
        .setup(|ctx, _ready, framework| {
            Box::pin(async move {
                poise::builtins::register_globally(ctx, &framework.options().commands).await?;
                let formatted_ip = format!("tcp://{}:{}", cfg_data.server_ip, cfg_data.server_port);
                Ok(Data {mappool: Mutex::new(vec![]), zmq_send_handle: Mutex::new(SocketHandle::new(zmq_comm::SocketType::DEALER, &formatted_ip, &cfg_data.rcon_password).expect("Failed to setup zmq"))})

            })
        });
    
    framework.run().await.unwrap();

}
