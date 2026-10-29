// The zoom key went down or up: the player's choice of key
// (`key.classic_zoom.zoom` in horizon-mods.txt), V by default.
fn classic_zoom_key(game: &mut crate::game::Game<'_>, key: &str, pressed: bool) {
    use crate::game::classic_zoom as zoom;
    // Turned off in Options > Mods: nothing until the next build leaves it out.
    if !game.native_on(zoom::ID) {
        return;
    }
    if key != game.native_mod_key(zoom::ID, zoom::KEY, zoom::DEFAULT_KEY) {
        return;
    }
    zoom::key(game.native_playing(), pressed);
}
