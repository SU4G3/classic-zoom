// The zoom in effect, unless another mod's came first.
fn classic_zoom_view(game: &crate::game::Game<'_>, zoom: &mut Option<crate::game::native_hooks::NativeZoom>) {
    if zoom.is_none()
        && game.native_on(crate::game::classic_zoom::ID)
        && let Some((factor, smooth, turn)) = crate::game::classic_zoom::view()
    {
        *zoom = Some(crate::game::native_hooks::NativeZoom {
            factor,
            smooth,
            turn,
        });
    }
}
