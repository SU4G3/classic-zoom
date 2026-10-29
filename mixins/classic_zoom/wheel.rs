// While the key is held, the wheel zooms instead of moving the hotbar.
fn classic_zoom_wheel(game: &crate::game::Game<'_>, steps: f32, claimed: &mut bool) {
    use crate::game::classic_zoom as zoom;
    if !*claimed && game.native_on(zoom::ID) && zoom::wheel(steps) {
        *claimed = true;
    }
}
