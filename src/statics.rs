pub struct StaticMessages {
    pub greeting: String, 

}

impl Default for StaticMessages {
    fn default() -> Self {
        StaticMessages{greeting: " 
        ***  I'M DA OAT BOT BABY  *** \n
        `★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★`\n
        __**Macros**__\n
        **/help**: *Help* - looking at it baby 
        **/list_mappool** : *Updates Pools* - Checks current mappool files on server, and updates the autocomplete list \n 
        **/current_mappool** : *List Pool* - Marco to see current map pool running on server, as well as the default \n 
        **/change_mappool** : *Change Current Mappool* - Updates the current mappool to the one specified \n
        **/rcon** : *Arbitrary Rcon commands* - Allows you to execute an arbitrary rcon command on the server \n
        `★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★`
        
        ".to_string()}
    }
}