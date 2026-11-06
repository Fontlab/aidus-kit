"""Run inside FontLab Python 3; reads only, no source or UI changes."""
import fontlab as fl


def inspect_current_font():
    font = fl.CurrentFont()
    if font is None:
        return {"font_open": False}
    package = fl.flPackage(font)
    return {"font_open": True, "package_id": int(package.fgId),
            "master": package.master, "masters": list(package.masters)}


if __name__ == "__main__":
    print(inspect_current_font())
