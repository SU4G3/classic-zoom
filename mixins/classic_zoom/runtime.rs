// SPDX-License-Identifier: GPL-3.0-or-later
// Classic Zoom, after WI Zoom's behaviour: hold the key (V by default) to
// zoom in 3x, turn the mouse wheel while holding it to zoom further in or
// out, and let go to snap back. The zoom is instant, and turning slows down
// in step with the zoom. Horizon caps the zoom at 10x, where WI Zoom goes to
// 50x. Adapted from Horizon's official native Zoom (MIT, see NOTICE). This
// file is both the mod's Cargo library (its tests) and the module the bundle
// adds to the game.
use std::cell::RefCell;

/// The mod's id: its key's line (`key.classic_zoom.zoom` in `horizon-mods.txt`).
pub const ID: &str = "classic_zoom";
pub const VERSION: &str = "2.0.0";
pub const DESCRIPTION: &str =
    "Hold V to zoom 3x, scroll for more, release to snap back. Instant, inspired by WI Zoom.";
/// The key's name, and its default.
pub const KEY: &str = "zoom";
pub const DEFAULT_KEY: &str = "key.keyboard.v";
/// The zoom the key starts at.
const START: f32 = 3.0;
/// The wheel's limits: no zoom, and Horizon's maximum.
const MIN: f32 = 1.0;
const MAX: f32 = 10.0;
/// Each wheel step multiplies the zoom by this.
const STEP: f32 = 1.1;

thread_local! {
    /// The zoom while the key is held; None when it is up.
    static HELD: RefCell<Option<f32>> = const { RefCell::new(None) };
}

/// The zoom key went down (only while playing) or up.
pub fn key(playing: bool, pressed: bool) {
    if pressed && !playing {
        return;
    }
    HELD.with_borrow_mut(|held| *held = pressed.then_some(START));
}

/// Wheel steps: true when the key is held and they zoom.
pub fn wheel(steps: f32) -> bool {
    HELD.with_borrow_mut(|held| {
        let Some(z) = held else {
            return false;
        };
        *z = (*z * STEP.powf(steps)).clamp(MIN, MAX);
        true
    })
}

/// The zoom in effect: (factor, smooth, turning scale), none when the key
/// is up. Never smooth, and turning slows in step with the zoom.
pub fn view() -> Option<(f32, bool, f32)> {
    HELD.with_borrow(|held| held.map(|factor| (factor, false, 1.0 / factor)))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn close(a: f32, b: f32) -> bool {
        (a - b).abs() < 1e-4
    }

    #[test]
    fn holds_at_three_and_lets_go() {
        key(false, true);
        assert_eq!(view(), None, "not while a screen is open");
        assert!(!wheel(1.0), "the wheel is the hotbar's while the key is up");
        key(true, true);
        assert_eq!(view(), Some((3.0, false, 1.0 / 3.0)));
        key(true, false);
        assert_eq!(view(), None);
        assert!(!wheel(1.0));
    }

    #[test]
    fn the_wheel_zooms_by_a_tenth_within_one_and_ten() {
        key(true, true);
        assert!(wheel(1.0));
        assert!(close(view().unwrap().0, 3.3));
        assert!(wheel(-2.0));
        assert!(close(view().unwrap().0, 3.3 / 1.21));
        assert!(wheel(100.0));
        assert_eq!(view().unwrap().0, 10.0);
        assert!(wheel(-100.0));
        assert_eq!(view().unwrap().0, 1.0);
        // Pressing again starts over at 3x.
        key(true, false);
        key(true, true);
        assert_eq!(view().unwrap().0, 3.0);
        key(true, false);
    }
}
