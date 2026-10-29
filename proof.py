"""Classic Zoom in a running modded game: the player's key choice holds (V does nothing once the key is
moved to C), C zooms, the wheel zooms further instead of moving the hotbar while C is held, and letting
go snaps back. Adapted from Horizon's official native Zoom proof (MIT, see NOTICE)."""
import json
import time
from game import Game, difference

# A player who moved the key to C, as the WebAssembly Classic Zoom kept it.
FILES = {"horizon-mods.txt": "key.classic_zoom.zoom:key.keyboard.c\n"}


def run(ctl, resources, out):
    with Game(ctl, resources, out, FILES) as g:
        results = {}
        g.run("options", "mods")
        assert "Classic Zoom 2.0.0: ON" in g.labels(), g.labels()
        g.shot("mods-page")
        g.play()
        g.run("command", "tp @s ~ ~ ~ 0 10")
        time.sleep(2)
        base = g.shot("1-normal")
        g.run("key", "v", "down")
        time.sleep(1)
        unbound = g.shot("2-v-not-bound")
        g.run("key", "v", "up")
        g.run("key", "c", "down")
        time.sleep(1)
        zoomed = g.shot("3-c-held-3x")
        slot = g.run("state")["selected"]
        g.run("scroll-at", "640", "360", "-5")
        time.sleep(1)
        further = g.shot("4-c-held-wheel")
        results["wheel_kept_slot_while_held"] = g.run("state")["selected"] == slot
        g.run("key", "c", "up")
        time.sleep(1)
        released = g.shot("5-released")
        g.run("scroll-at", "640", "360", "-1")
        results["wheel_moves_slot_after"] = g.run("state")["selected"] != slot
        results["diff_unbound_key"] = round(difference(base, unbound), 1)
        results["diff_zoomed"] = round(difference(base, zoomed), 1)
        results["diff_wheel_vs_zoomed"] = round(difference(zoomed, further), 1)
        results["diff_released"] = round(difference(base, released), 1)
        noise = max(results["diff_unbound_key"], results["diff_released"], 1)
        assert results["wheel_kept_slot_while_held"] and results["wheel_moves_slot_after"], results
        assert results["diff_zoomed"] > 3 * noise, results
        assert results["diff_wheel_vs_zoomed"] > 2 * noise, results
        print(json.dumps({"proof": "classic_zoom", "ok": True, **results}, indent=2))
