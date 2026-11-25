import glob
import os
import re
from pathlib import Path

# Match font-size declarations:
# Matches font-size : <value> [!important] [; or } or end of string]
DECL_RE = re.compile(
    r'(font-size\s*:\s*)'
    r'('
    r'clamp\s*\([^;!}]+?\)'
    r'|'
    r'calc\s*\([^;!}]+?\)'
    r'|'
    r'[^;!}]+'
    r')'
    r'(\s*!important)?',
    re.IGNORECASE
)

def transform_css_text(css_text):
    changes = 0

    def replacer(match):
        nonlocal changes
        prefix = match.group(1)
        val = match.group(2).strip()
        important = match.group(3) or ''

        # 1. Already calc(...): leave alone
        if re.match(r'^calc\s*\(', val, re.IGNORECASE):
            return match.group(0)

        # 2. clamp(...)
        if re.match(r'^clamp\s*\(', val, re.IGNORECASE):
            inner_m = re.match(r'^clamp\s*\((.*)\)$', val, re.IGNORECASE | re.DOTALL)
            if not inner_m:
                return match.group(0)
            inner = inner_m.group(1)

            # Replace px values inside clamp if not already in calc()
            def clamp_arg_replacer(m):
                px_val = m.group(1)
                return f"calc({px_val} * var(--bb-scale))"

            new_inner, sub_count = re.subn(
                r'(?<!calc\()\b([1-9][0-9]*(?:\.[0-9]+)?px)\b(?!\s*\* var\(--bb-scale\))',
                clamp_arg_replacer,
                inner
            )
            if sub_count > 0:
                changes += 1
                return f"{prefix}clamp({new_inner}){important}"
            return match.group(0)

        # 3. Simple px value: e.g. "13px", "14.5px"
        px_match = re.match(r'^([1-9][0-9]*(?:\.[0-9]+)?px)$', val, re.IGNORECASE)
        if px_match:
            px_val = px_match.group(1)
            changes += 1
            return f"{prefix}calc({px_val} * var(--bb-scale)){important}"

        # Otherwise leave unchanged (e.g. rem, em, %, inherit)
        return match.group(0)

    transformed = DECL_RE.sub(replacer, css_text)
    return transformed, changes

def process_file(file_path, dry_run=False):
    path = Path(file_path)
    original_text = path.read_text(encoding='utf-8', errors='ignore')

    # If HTML file, transform within <style> tags and inline style attributes
    if path.suffix.lower() == '.html':
        total_changes = 0
        
        # Transform <style> blocks
        def style_tag_sub(m):
            nonlocal total_changes
            block_content = m.group(1)
            transformed_block, count = transform_css_text(block_content)
            total_changes += count
            return f"<style{m.group(2)}>{transformed_block}</style>"

        text_after_blocks = re.sub(
            r'<style([^>]*)>(.*?)</style>',
            lambda m: f"<style{m.group(1)}>{transform_css_text(m.group(2))[0]}</style>",
            original_text,
            flags=re.DOTALL | re.IGNORECASE
        )
        # Recount for blocks
        _, block_changes = transform_css_text(
            "\n".join(re.findall(r'<style[^>]*>(.*?)</style>', original_text, flags=re.DOTALL | re.IGNORECASE))
        )
        total_changes += block_changes

        # Transform inline style="..." attributes
        def inline_style_sub(m):
            nonlocal total_changes
            quote = m.group(1)
            style_content = m.group(2)
            transformed_style, count = transform_css_text(style_content)
            total_changes += count
            return f'style={quote}{transformed_style}{quote}'

        final_text = re.sub(
            r'style=([\"\'])(.*?)\1',
            inline_style_sub,
            text_after_blocks,
            flags=re.IGNORECASE
        )

        if not dry_run and total_changes > 0:
            path.write_text(final_text, encoding='utf-8')
        return total_changes

    else:
        # Standard CSS file
        transformed_text, changes = transform_css_text(original_text)
        if not dry_run and changes > 0:
            path.write_text(transformed_text, encoding='utf-8')
        return changes

def main():
    css_files = sorted(glob.glob('static/css/*.css'))
    # Exclude vendor and bb-typography.css
    css_files = [f for f in css_files if 'vendor' not in f and not f.endswith('bb-typography.css')]
    
    html_files = sorted(glob.glob('templates/**/*.html', recursive=True))

    print(f"Scanning {len(css_files)} CSS files and {len(html_files)} HTML template files...")
    
    file_changes = {}
    total_declarations = 0

    for f in css_files:
        changes = process_file(f, dry_run=False)
        if changes > 0:
            file_changes[f] = changes
            total_declarations += changes
            print(f"  {f}: {changes} declarations converted")
        else:
            print(f"  {f}: 0 declarations")

    template_changes = 0
    for f in html_files:
        changes = process_file(f, dry_run=False)
        if changes > 0:
            file_changes[f] = changes
            total_declarations += changes
            template_changes += changes
            print(f"  {f}: {changes} declarations converted")

    print(f"\nTotal font-size declarations converted: {total_declarations}")

    # Idempotency check: run again and verify 0 changes
    print("\nVerifying idempotency (second pass)...")
    second_pass_changes = 0
    for f in css_files:
        c2 = process_file(f, dry_run=True)
        second_pass_changes += c2
        if c2 > 0:
            print(f"  WARNING: {f} had {c2} changes on second pass!")
    for f in html_files:
        c2 = process_file(f, dry_run=True)
        second_pass_changes += c2
        if c2 > 0:
            print(f"  WARNING: {f} had {c2} changes on second pass!")

    if second_pass_changes == 0:
        print("Idempotency verified: 0 changes on second pass!")
    else:
        print(f"ERROR: Idempotency failed with {second_pass_changes} changes on second pass!")

if __name__ == '__main__':
    main()

