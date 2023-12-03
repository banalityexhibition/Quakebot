use std::fmt::Display;
use std::fs::File; 
use std::io::{self, BufRead};
use std::path::Path;

#[derive (Default)]
pub struct ConfigData {
    pub discord_token: String,
    pub server_ip: String, 
    pub server_port: String,
    pub rcon_password: String,
}

pub fn read_config_data(filepath: String) -> Option<ConfigData>{
    let mut out = ConfigData {..Default::default() };
    if let Ok(lines) = read_lines(filepath) {
        for line in lines {
            if let Ok(ip) = line {
                if ip.starts_with("#") {
                }
                else if ip.starts_with("discord_token:"){
                    let vals: Vec<&str> = ip.split(" ").collect();
                    out.discord_token = vals[1].to_string();

                }
                else if ip.starts_with("server_ip:") {
                    let vals: Vec<&str> = ip.split(" ").collect();
                    out.server_ip = vals[1].to_string();
                }
                else if ip.starts_with("server_port:"){
                    let vals: Vec<&str> = ip.split(" ").collect();
                    out.server_port = vals[1].to_string();
                }
                else if ip.starts_with("rcon_password"){
                    let vals: Vec<&str> = ip.split(" ").collect();
                    out.rcon_password = vals[1].to_string();
                }
                else {
                    println!("Unknown config line: {}", ip);
                }

            }
            else {
                return None;
            }
              }
    }
    Some(out)
}

fn read_lines<T>(filepath: T) -> io::Result<io::Lines<io::BufReader<File>>>
where T: AsRef<Path>, {
    let file = File::open(filepath)?;
    Ok(io::BufReader::new(file).lines())
}

pub struct MapPoolDisplay {
    pub map_pool: Vec<String>,
}

impl MapPoolDisplay {
    pub fn new(map_pool: Vec<String>) -> Self {
        Self {
            map_pool,
        }
    }

}

impl Display for MapPoolDisplay {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let mut out = String::new();
        for map in &self.map_pool {
            out.push_str(&format!("* {}\n", map));
        }
        write!(f, "{}", out)
    }
}