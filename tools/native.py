#!/usr/bin/env python3
"""Build Horizon's native mods (native/<name>/) into Horizon, package them, and prove them in a running game.

    python3 native/tools/native.py check zoom             # apply on the pinned Horizon, cargo check the game
    python3 native/tools/native.py check zoom minimap ... # several mods applied together, as a player's set is
    python3 native/tools/native.py build zoom             # ... and build it (fast profile); prints the binary
    python3 native/tools/native.py package zoom           # native/target/<id>-<version>.hnmod for the registry
    python3 native/tools/native.py proof --resources PATH zoom   # build, then drive the game with horizon-ctl
    --horizon REV   build on another Horizon commit (`latest` = the newest Nightly) instead of the mods'
                    compatibility.json: they use only the native hook points, so they build on any Horizon whose
                    NATIVE_HOOKS_API is at least the one they name, as the launcher does. Without it, mods pinned
                    to different commits build on the commit of those that need the most hook points.
    `all` names every mod in native/.

Horizon's source comes from GitHub's archive of the commit, never a local checkout; horizon-mixins is built once at
the pinned commit. Everything goes under native/target/, shared by the mods.
"""
import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tomllib
import urllib.request
import zipfile
from pathlib import Path

# Vendored from horizon-rust/horizon-mods native/tools (MIT, see NOTICE): here the repository root is the
# one mod, so its name on the command line is `.`.
NATIVE = Path(__file__).resolve().parents[1]
TARGET = NATIVE / "target"
REPO = "horizon-rust/horizon"
HOOKS_FILE = "crates/horizon-client/src/game/native_hooks.rs"
HOOKS_LINE = re.compile(r"^pub\(crate\) const NATIVE_HOOKS_API: u32 = (\d+);$", re.M)


class Mod:
    """native/<name>/: its compatibility.json and its one mixin bundle."""

    def __init__(self, name):
        self.root = NATIVE / name
        if not (self.root / "compatibility.json").is_file():
            sys.exit(f"no mod native/{name}/ (compatibility.json)")
        self.compat = json.loads((self.root / "compatibility.json").read_text())
        mixins = self.root / "mixins"
        self.bundle = next(p for p in mixins.iterdir() if (p / "horizon-mixin.toml").is_file())
        manifest = tomllib.loads((self.bundle / "horizon-mixin.toml").read_text())
        self.manifest = manifest
        self.id = manifest["mod"]["id"]
        self.version = manifest["mod"]["version"]


def all_mods():
    return sorted(p.name for p in NATIVE.iterdir() if (p / "compatibility.json").is_file())


def log(*args):
    print(*args, file=sys.stderr, flush=True)


def get(url):
    request = urllib.request.Request(url, headers={"User-Agent": "horizon-native-mod"})
    token = os.environ.get("GITHUB_TOKEN")
    if token and url.startswith("https://api.github.com/"):
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=300) as response:
        return response.read()


def latest_nightly():
    """The commit of the newest Nightly: its permanent nightly-source/<date>-<short> tag."""
    refs = json.loads(get(f"https://api.github.com/repos/{REPO}/git/matching-refs/tags/nightly-source/"))
    newest = max(refs, key=lambda r: r["ref"])
    return get_commit(newest["ref"].removeprefix("refs/tags/"))


def get_commit(ref):
    return json.loads(get(f"https://api.github.com/repos/{REPO}/commits/{ref}"))["sha"]


def source(revision):
    """Horizon's source at `revision`, unpacked once into target/horizon/<revision>/."""
    out = TARGET / "horizon" / revision
    if (out / ".horizon-revision").is_file():
        return out
    log(f"Downloading Horizon {revision[:7]}")
    data = get(f"https://codeload.github.com/{REPO}/tar.gz/{revision}")
    partial = TARGET / "horizon" / f".{revision}.partial"
    shutil.rmtree(partial, ignore_errors=True)
    partial.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        archive.extractall(partial, filter="data")
    top = next(partial.iterdir())
    # horizon-mixins refuses links; the source has a few (docs), none needed to build.
    for path in top.rglob("*"):
        if path.is_symlink():
            path.unlink()
    (top / ".horizon-revision").write_text(revision)
    shutil.rmtree(out, ignore_errors=True)
    top.rename(out)
    shutil.rmtree(partial)
    return out


def hooks_api(tree):
    found = HOOKS_LINE.search((tree / HOOKS_FILE).read_text()) if (tree / HOOKS_FILE).is_file() else None
    return int(found.group(1)) if found else None


def tool(mods):
    """horizon-mixins at the mods' pinned commit, built once."""
    revs = {m.compat["horizon_mixins_revision"] for m in mods}
    if len(revs) != 1:
        sys.exit(f"the mods pin different horizon-mixins commits: {sorted(revs)}")
    rev = revs.pop()
    root = TARGET / "horizon-mixins" / rev
    binary = root / "bin" / "horizon-mixins"
    if not binary.is_file():
        log(f"Building horizon-mixins {rev[:7]}")
        repo = mods[0].compat["horizon_mixins_repository"]
        subprocess.run(["cargo", "install", "--locked", "--quiet", "--git", repo, "--rev", rev, "--root", str(root),
                        "horizon-mixins-cli"], check=True)
    return binary


def stage(mods, revision):
    """The mods applied together on Horizon `revision`: target/stage/<ids>/ (cargo's incremental state survives)."""
    tree = source(revision)
    api = hooks_api(tree)
    # Hook points are only ever added: any later version has the ones these mods hook.
    for m in mods:
        if api is None or api < m.compat["hooks"]:
            sys.exit(f"Horizon {revision[:7]} has native hook points v{api}, {m.id} needs v{m.compat['hooks']}.")
    key = "+".join(m.id for m in mods)
    # As the launcher does for mods on the hook points: pin the copies to the commit they build on.
    bundles = TARGET / "mods" / key
    shutil.rmtree(bundles, ignore_errors=True)
    for m in mods:
        shutil.copytree(m.bundle, bundles / m.id)
        toml = bundles / m.id / "horizon-mixin.toml"
        toml.write_text(re.sub(r'horizon_revision = "[0-9a-f]{40}"', f'horizon_revision = "{revision}"',
                               toml.read_text()))
    fresh = (TARGET / "stage.new").resolve()
    shutil.rmtree(fresh, ignore_errors=True)
    subprocess.run([str(tool(mods)), "apply", "--workspace", str(tree), "--mods", str(bundles), "--out", str(fresh)],
                   check=True, stdout=subprocess.DEVNULL)
    out = TARGET / "stage" / key
    out.mkdir(parents=True, exist_ok=True)
    # Only changed files are replaced, so cargo rebuilds only what changed.
    subprocess.run(["rsync", "-a", "--checksum", "--delete", f"{fresh}/", f"{out}/"], check=True)
    shutil.rmtree(fresh)
    return out


def cargo(stage_dir, action):
    jobs = os.environ.get("FLEET_LOAD_JOBS") or os.environ.get("CARGO_BUILD_JOBS")
    command = ["cargo", action, "--locked", "-p", "horizon-client", "--bin", "horizon-client"]
    if action == "build":
        command += ["--bin", "horizon-ctl", "--profile", "fast"]
    if os.environ.get("NATIVE_NO_DEFAULT_FEATURES"):
        command.append("--no-default-features")
    if jobs:
        command += ["-j", jobs]
    env = dict(os.environ, CARGO_TARGET_DIR=str(TARGET / "cargo"), RUSTFLAGS="-D warnings")
    subprocess.run(command, cwd=stage_dir, env=env, check=True)
    return TARGET / "cargo" / "fast"


def package(m):
    """A deterministic .hnmod: horizon-native.json and the bundle's .rs and .toml files."""
    manifest = {"schema": 1, "id": m.id, "version": m.version, "game": m.compat["game"],
                "horizon": m.compat["horizon_revision"], "mixins": m.compat["horizon_mixins_revision"],
                "hooks": m.compat["hooks"]}
    pinned = m.manifest.get("compatibility", {}).get("horizon_revision")
    if pinned != m.compat["horizon_revision"]:
        sys.exit(f"{m.id}: horizon-mixin.toml pins {pinned}, compatibility.json {m.compat['horizon_revision']}")
    files = {"horizon-native.json": (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()}
    for path in sorted(m.bundle.iterdir()):
        if path.suffix in (".rs", ".toml"):
            files[f"mixins/{m.id}/{path.name}"] = path.read_bytes()
    out = TARGET / f"{m.id}-{m.version}.hnmod"
    TARGET.mkdir(exist_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content)
    print(json.dumps({"file": str(out), "size": out.stat().st_size,
                      "sha256": hashlib.sha256(out.read_bytes()).hexdigest()}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", choices=["check", "build", "package", "proof"])
    parser.add_argument("mods", nargs="+", help="folders of native/ (`all`: every one)")
    parser.add_argument("--horizon", help="a Horizon commit, `latest` (newest Nightly) or a tag (default: the mods' own)")
    parser.add_argument("--resources", help="prepared resources (proof): .local/horizon-client/26.3")
    args = parser.parse_args()
    names = all_mods() if args.mods == ["all"] else args.mods
    mods = [Mod(n) for n in names]
    if args.action == "package":
        for m in mods:
            package(m)
        return
    if args.horizon is None:
        # Mods on the hook points build on any Horizon with the hook points they need, as the launcher builds
        # them: the commit of the mods that need the most has them all (stage checks each mod's need).
        newest = max(m.compat["hooks"] for m in mods)
        revs = {m.compat["horizon_revision"] for m in mods if m.compat["hooks"] == newest}
        if len(revs) != 1:
            sys.exit(f"the mods were tested on different Horizons {sorted(revs)}: pass --horizon")
        revision = revs.pop()
    else:
        revision = latest_nightly() if args.horizon == "latest" else args.horizon
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        revision = get_commit(revision)
    log(f"{', '.join(f'{m.id} {m.version}' for m in mods)} on Horizon {revision[:7]}")
    out = stage(mods, revision)
    if args.action == "check":
        cargo(out, "check")
        print(json.dumps({"mods": [m.id for m in mods], "horizon": revision, "check": "ok"}))
        return
    binaries = cargo(out, "build")
    if args.action == "build":
        print(json.dumps({"mods": [m.id for m in mods], "horizon": revision, "game": str(binaries / "horizon-client")}))
        return
    if not args.resources:
        sys.exit("proof needs --resources (prepared resources for Minecraft 26.3)")
    sys.path.insert(0, str(Path(__file__).parent))
    import importlib.util
    for m in mods:
        spec = importlib.util.spec_from_file_location(f"proof_{m.id}", m.root / "proof.py")
        proof = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(proof)
        proof.run(binaries / "horizon-ctl", Path(args.resources).resolve(), TARGET / "proof" / m.id)


if __name__ == "__main__":
    main()
