#!/usr/bin/env python3
import os
import shutil
from pathlib import Path
import re
import plistlib

def read_file_any(path: Path):
    """Read file as XML plist or plain text."""
    text = path.read_text(encoding="utf-8")
    if text.strip().startswith("<?xml"):
        with open(path, "rb") as f:
            return plistlib.load(f), "xml"
    else:
        return text, "text"

def write_file_any(path: Path, data, fmt):
    """Write file in same format it was read."""
    if fmt == "xml":
        with open(path, "wb") as f:
            plistlib.dump(data, f)
    else:
        path.write_text(data, encoding="utf-8")

def change_family_name(fontinfo_path: Path, new_name: str):
    try:
        data, fmt = read_file_any(fontinfo_path)
        if fmt == "xml":
            data["familyName"] = new_name
        else:
            # replace or insert familyName line in text plist
            if "familyName" in data:
                data = re.sub(r'familyName = .*?;', f'familyName = "{new_name}";', data)
            else:
                data = re.sub(r'\{', f'{{\nfamilyName = "{new_name}";', data, count=1)
        write_file_any(fontinfo_path, data, fmt)
        print(f"✏️  Family name changed to {new_name}")
    except Exception as e:
        print(f"⚠️  Could not modify family name: {e}")

def read_glyph_file(path: Path):
    """Read glyph file and return data with format."""
    text = path.read_text(encoding="utf-8")
    if text.strip().startswith("<?xml"):
        with open(path, "rb") as f:
            return plistlib.load(f), "xml"
    else:
        return text, "text"

def write_glyph_file(path: Path, data, fmt):
    """Write glyph file."""
    if fmt == "xml":
        with open(path, "wb") as f:
            plistlib.dump(data, f)
    else:
        path.write_text(data, encoding="utf-8")

def parse_openstep_dict(text, start_pos=0):
    """Parse OpenStep plist dict format and return dict with positions."""
    result = {}
    pos = text.find('{', start_pos)
    if pos == -1:
        return None, start_pos
    
    pos += 1  # Skip '{'
    depth = 1
    current_key = None
    
    while pos < len(text) and depth > 0:
        # Skip whitespace
        while pos < len(text) and text[pos] in ' \t\n\r':
            pos += 1
        
        if pos >= len(text):
            break
            
        char = text[pos]
        
        if char == '}':
            depth -= 1
            if depth == 0:
                return result, pos + 1
            pos += 1
            
        elif char == '{':
            depth += 1
            pos += 1
            
        else:
            # Try to read key = value;
            key_match = re.match(r'(\w+)\s*=', text[pos:])
            if key_match:
                key = key_match.group(1)
                pos += key_match.end()
                
                # Skip whitespace
                while pos < len(text) and text[pos] in ' \t\n\r':
                    pos += 1
                
                # Find value end (semicolon at same depth)
                value_start = pos
                paren_depth = 0
                brace_depth = 0
                in_string = False
                escape = False
                
                while pos < len(text):
                    if escape:
                        escape = False
                        pos += 1
                        continue
                    
                    c = text[pos]
                    
                    if c == '\\':
                        escape = True
                    elif c == '"':
                        in_string = not in_string
                    elif not in_string:
                        if c == '(':
                            paren_depth += 1
                        elif c == ')':
                            paren_depth -= 1
                        elif c == '{':
                            brace_depth += 1
                        elif c == '}':
                            brace_depth -= 1
                        elif c == ';' and paren_depth == 0 and brace_depth == 0:
                            result[key] = (value_start, pos)
                            pos += 1
                            break
                    
                    pos += 1
            else:
                pos += 1
    
    return result, pos

def extract_layers_text(ss01_text, base_text):
    """Extract layers from ss01 and prepare for insertion into base."""
    # Parse both files to find layers positions
    ss01_parts, _ = parse_openstep_dict(ss01_text)
    base_parts, _ = parse_openstep_dict(base_text)
    
    if not ss01_parts or 'layers' not in ss01_parts:
        return None
    if not base_parts or 'layers' not in base_parts:
        return None
    
    # Extract layers value from ss01
    ss01_layers_start, ss01_layers_end = ss01_parts['layers']
    ss01_layers_value = ss01_text[ss01_layers_start:ss01_layers_end].strip()
    
    # Get position in base file
    base_layers_start, base_layers_end = base_parts['layers']
    
    # Replace in base file
    new_base = (
        base_text[:base_layers_start] +
        ss01_layers_value +
        base_text[base_layers_end:]
    )
    
    return new_base

def replace_with_ss01(glyphs_dir: Path):
    """Replace layers in base glyphs with their .ss01 variants."""
    replaced = 0
    skipped = 0
    
    # Collect all ss01 files
    ss01_files = list(glyphs_dir.glob("*.ss01.glyph"))
    print(f"Found {len(ss01_files)} .ss01 glyph files")
    
    for i, glyph_file in enumerate(ss01_files, 1):
        base_name = glyph_file.stem.replace(".ss01", "")
        base_path = glyphs_dir / f"{base_name}.glyph"
        
        print(f"[{i}/{len(ss01_files)}] Processing {base_name}...", end=" ", flush=True)
        
        if not base_path.exists():
            print("❌ base not found")
            skipped += 1
            continue
        
        try:
            # Read both files
            ss01_data, ss01_fmt = read_glyph_file(glyph_file)
            base_data, base_fmt = read_glyph_file(base_path)
            
            if ss01_fmt == "xml" and base_fmt == "xml":
                # XML format - direct copy of layers key
                if "layers" in ss01_data:
                    base_data["layers"] = ss01_data["layers"]
                    write_glyph_file(base_path, base_data, base_fmt)
                    print("✅")
                    replaced += 1
                else:
                    print("⚠️  no layers")
                    skipped += 1
                    
            elif ss01_fmt == "text" and base_fmt == "text":
                # Text format - use custom parser
                new_base = extract_layers_text(ss01_data, base_data)
                
                if new_base:
                    write_glyph_file(base_path, new_base, base_fmt)
                    print("✅")
                    replaced += 1
                else:
                    print("⚠️  parse failed")
                    skipped += 1
            else:
                print(f"⚠️  format mismatch")
                skipped += 1
                
        except Exception as e:
            print(f"❌ {str(e)[:50]}")
            skipped += 1
    
    if skipped > 0:
        print(f"\n⚠️  Skipped {skipped} glyph(s)")
    return replaced

def main(src_pkg, dst_pkg):
    src = Path(src_pkg)
    dst = Path(dst_pkg)
    
    if not src.exists():
        print(f"❌ Source package not found: {src_pkg}")
        return False
    
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print(f"📦 Copied {src_pkg} → {dst_pkg}")

    # Change family name in fontinfo
    fontinfo = dst / "fontinfo.plist"
    if fontinfo.exists():
        change_family_name(fontinfo, "Stack Sans Notch")
    else:
        print("⚠️  fontinfo.plist not found")

    # Replace glyphs with .ss01 variants
    glyphs_dir = dst / "glyphs"
    if not glyphs_dir.exists():
        print("❌ glyphs directory not found")
        return False
        
    replaced = replace_with_ss01(glyphs_dir)
    print(f"\n✨ Replaced {replaced} glyph(s) with their .ss01 versions.")
    print("✅ Stack Sans Notch source ready.")
    return True

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: prepare_notch.py <source.glyphspackage> <dest.glyphspackage>")
        sys.exit(1)
    success = main(sys.argv[1], sys.argv[2])
    sys.exit(0 if success else 1)
    