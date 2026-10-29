//! Classic Zoom, after WI Zoom's behaviour: hold the key (V by default) to
//! zoom in 3x, turn the mouse wheel while holding it to zoom further in or
//! out, and let go to snap back. The zoom is instant, and turning slows down
//! in step with the zoom, as in WI Zoom. Horizon caps the zoom at 10x, where
//! WI Zoom goes to 50x.
use horizon_mod_sdk::{
    Mod, Registration,
    input::{self, Event},
    render::{self, Zoom as ZoomView},
};

/// The key's name for `register-key`.
const KEY: &str = "zoom";
/// The zoom the key starts at.
const START: f32 = 3.0;
/// The wheel's limits: no zoom, and Horizon's maximum.
const MIN: f32 = 1.0;
const MAX: f32 = 10.0;
/// Each wheel step multiplies the zoom by this.
const STEP: f32 = 1.1;

struct ClassicZoom {
    /// The zoom while the key is held; None when it is up.
    held: Option<f32>,
}

impl ClassicZoom {
    /// Tells the game the zoom in effect.
    fn show(&self) {
        let factor = self.held.unwrap_or(1.0);
        render::set_zoom(ZoomView {
            factor,
            smooth: false,
            turn: 1.0 / factor,
        });
    }
}

impl Mod for ClassicZoom {
    fn init() -> Result<(Self, Registration), String> {
        input::register_key(KEY, "Zoom key", "key.keyboard.v")?;
        Ok((ClassicZoom { held: None }, Registration::new().on_frame()))
    }
    fn frame(&mut self, _seconds: f32) {
        let mut changed = false;
        for event in input::poll() {
            match event {
                Event::KeyDown(k) if k == KEY => {
                    self.held = Some(START);
                    // While held, the wheel zooms instead of moving the hotbar.
                    input::claim_wheel(true);
                }
                Event::KeyUp(k) if k == KEY => {
                    self.held = None;
                    input::claim_wheel(false);
                }
                Event::Wheel(steps) => {
                    let Some(z) = &mut self.held else { continue };
                    *z = (*z * STEP.powf(steps)).clamp(MIN, MAX);
                }
                _ => continue,
            }
            changed = true;
        }
        if changed {
            self.show();
        }
    }
}

horizon_mod_sdk::export_mod!(ClassicZoom);
