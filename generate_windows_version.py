#!/usr/bin/env python3
"""Generate PyInstaller Windows version metadata from VERSION."""

from pathlib import Path


def main() -> None:
    project = Path(__file__).resolve().parent
    version = (project / "VERSION").read_text(encoding="ascii").strip()
    numeric = version.split("-", 1)[0].split("+")[0]
    parts = [int(part) for part in numeric.split(".")]
    if len(parts) > 4:
        raise ValueError("VERSION must contain no more than four numeric parts")
    parts.extend([0] * (4 - len(parts)))
    version_tuple = tuple(parts)

    output_dir = project / ".build-meta"
    output_dir.mkdir(exist_ok=True)
    output = output_dir / "windows_version_info.txt"
    output.write_text(
        f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={version_tuple},
    prodvers={version_tuple},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [
          StringStruct('CompanyName', 'ImageStitcher contributors'),
          StringStruct('FileDescription', 'ImageStitcher'),
          StringStruct('FileVersion', '{version}'),
          StringStruct('InternalName', 'ImageStitcher'),
          StringStruct('OriginalFilename', 'ImageStitcher.exe'),
          StringStruct('ProductName', 'ImageStitcher'),
          StringStruct('ProductVersion', '{version}')
        ]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
""",
        encoding="utf-8",
    )
    print(f"Generated {output}")


if __name__ == "__main__":
    main()
