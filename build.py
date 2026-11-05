import shutil
import re
from pathlib import Path
import sys

Import("env")


def read_firmware_version(project_dir):
    config_path = project_dir / "src" / "CONFIG.h"
    try:
        config_text = config_path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"ERROR: Unable to read firmware version from {config_path}: {e}")
        sys.exit(1)

    match = re.search(r'static\s+const\s+char\s*\*\s*FIRMWARE\s*=\s*"([^"]+)"', config_text)
    if not match:
        print(f'ERROR: FIRMWARE value was not found in {config_path}')
        sys.exit(1)

    return match.group(1)


def get_display_suffix(build_env):
    pio_env = build_env.get("PIOENV", "").lower()
    if "ssd1306" in pio_env:
        return "ssd"
    if "sh1106" in pio_env:
        return "sh"
    return "display"


def export_factory_binary(source, target, env):
    project_dir = Path(env["PROJECT_DIR"])
    build_dir = Path(env.subst("$BUILD_DIR"))
    firmware_version = read_firmware_version(project_dir)
    display_suffix = get_display_suffix(env)

    factory_bin = build_dir / "firmware.factory.bin"
    normal_bin = build_dir / "firmware.bin"
    output_bin = project_dir / f"esp-hack_{firmware_version}-{display_suffix}.bin"

    # Arduino-ESP32 / PlatformIO already creates firmware.factory.bin for this
    # ESP32-S3 target. Reuse it instead of requiring a bundled esptool.exe.
    source_bin = factory_bin if factory_bin.exists() else normal_bin

    if not source_bin.exists():
        print(f"WARNING: no binary available to export from {build_dir}")
        return

    shutil.copy2(source_bin, output_bin)
    print(f"Exported flash image: {output_bin}")
    print(f"Source image: {source_bin}")


env.AddPostAction("$BUILD_DIR/${PROGNAME}.bin", export_factory_binary)
