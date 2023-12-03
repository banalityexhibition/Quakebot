use futures::{Stream, StreamExt};
use crate::serenity_structs::*;
use crate::utils::MapPoolDisplay;
use crate::statics::StaticMessages;

/// Autocomplete the mappool with the ones which currently exist on the server 
/// Mappool data is passed through the global context
async fn autocomplete_mappool<'a>(
    ctx: Context<'_>,
    partial: &'a str,
) -> impl Stream<Item = String> + 'a {
    let mappool = ctx.data().mappool.lock().await;
    futures::stream::iter(mappool.to_owned())
        .filter(move |map_name| futures::future::ready(map_name.starts_with(partial)))
        .map(|map_name| map_name.to_string())
}

/// Change the current mappool. 
#[poise::command(slash_command)]
pub async fn change_mappool(
    ctx: Context<'_>,
    #[description = "Map to change to"] 
    #[autocomplete = "autocomplete_mappool"]
    map_name: String,
) -> Result<(), Error> {
    ctx.data().zmq_send_handle.lock().await.send(format!("set sv_mappoolfile {}", map_name));
    ctx.data().zmq_send_handle.lock().await.send("reload_mappool".to_string());
    ctx.data().zmq_send_handle.lock().await.send("startrandommap".to_string());
    let response = format!("### Changing Mappool to: \n> {}", map_name);
    ctx.say(response).await?;
    Ok(())
}

///Perform a generic rcon command
#[poise::command(slash_command)]
pub async fn rcon(
    ctx: Context<'_>,
    #[description = "Command to send to the server"] 
    command: String,
) -> Result<(), Error> {
    ctx.data().zmq_send_handle.lock().await.send(command);
    let mut data_in = ctx.data().zmq_send_handle.lock().await.recv();
    let mut server_response= vec![]; 
    loop {
        if data_in.is_none() || data_in.clone().unwrap().len() < 1  {
            data_in = ctx.data().zmq_send_handle.lock().await.recv();
        }
        else {
            server_response.push(data_in.clone().unwrap());
            while data_in.clone().is_some() && data_in.clone().unwrap().len() > 0 {
                data_in = ctx.data().zmq_send_handle.lock().await.recv();
                match data_in.clone() {
                    Some(data) => server_response.push(data),
                    None => {},
                }
            }
            break;
        }
    }
    let response = format!("### Server Response: \n> {:?}", server_response);
    ctx.say(response).await?;
    Ok(())
}

/// Lists the current mappool  
#[poise::command(slash_command)]
pub async fn current_mappool(
    ctx: Context<'_>,
) -> Result<(), Error> {
    ctx.data().zmq_send_handle.lock().await.send(format!("sv_mappoolfile"));
    let mut data_in = ctx.data().zmq_send_handle.lock().await.recv();
    let server_response; 
    loop {
        if data_in.is_none() || data_in.clone().unwrap().len() < 1  {
            data_in = ctx.data().zmq_send_handle.lock().await.recv();
        }
        else {
            if data_in.clone().unwrap().contains(".txt"){
                server_response = data_in.unwrap()[21..].to_string();
                break;
            }
        }
    }
    let map_data = server_response.split("\"").collect::<Vec<&str>>();

    //Strip out the color codes
    let current_mp = map_data[0].to_string().replace("^7", "");
    let default_mp = map_data[2].to_string().replace("^7", "");
    

    let response = format!("## Current Mappool \n * {} \n \n## Default \n * {}", current_mp, default_mp);
    ctx.say(response).await?;
    Ok(())
}


/// Reads the current mapools available on the server and updates the global context to include them.
#[poise::command(slash_command)]
pub async fn list_mappool(
    ctx: Context<'_>,
) -> Result<(), Error> {
    ctx.data().zmq_send_handle.lock().await.send("fdir /mappool*".to_string());
    let mut maplist = Vec::new();
    let mut data_in = ctx.data().zmq_send_handle.lock().await.recv();
    loop {
        if data_in.is_none() || data_in.clone().unwrap().len() < 1  {
            data_in = ctx.data().zmq_send_handle.lock().await.recv();
        }
        else if data_in.clone().unwrap().contains("listed") {
            break;        
        }
        else {
            if data_in.clone().unwrap().contains(".txt"){

                let len = data_in.clone().unwrap().len();
                maplist.push(data_in.unwrap()[1..len - 1].to_string());
            }
            data_in = ctx.data().zmq_send_handle.lock().await.recv();

        }
    }

    {
        let mut data = ctx.data().mappool.lock().await;
        *data = maplist.clone();
    }
    let response = format!("## Current Mappool \n \n {}", MapPoolDisplay::new(maplist));
    ctx.say(response).await?;
    Ok(())
}

/// Displays the help message
#[poise::command(slash_command)]
pub async fn help(
    ctx: Context<'_>,
) -> Result<(), Error> {
    ctx.say(StaticMessages::default().greeting).await?;
    Ok(())
}