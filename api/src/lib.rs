use curse_client::mod_api::{Hooks, Host, PlayerLoggedInEvent, Text};

pub fn hooks() -> Box<dyn Hooks> {
    Box::new(Mod)
}

struct Mod;

impl Hooks for Mod {
    fn player_logged_in(&self, host: &mut dyn Host, event: &mut PlayerLoggedInEvent<'_>) {
        host.tell(event.player, Text::literal(greeting(event.name)));
    }
}

pub fn greeting(name: &str) -> String {
    format!("example_mod says hello, {name}!")
}

#[cfg(test)]
mod tests {
    use super::greeting;

    #[test]
    fn greeting_names_the_player() {
        assert_eq!(greeting("Alex"), "example_mod says hello, Alex!");
    }
}
