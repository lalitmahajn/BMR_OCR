from pathlib import Path
import re
import shutil


def rename_files():
    images_dir = Path("data/images")
    # Pattern: HASH_pNUMBER.ext
    # We want: pNUMBER_HASH.ext
    # Example: b9dea..._p1.jpg -> p1_b9dea...jpg

    # Iterate over all files
    for file_path in images_dir.glob("*"):
        if file_path.is_dir():
            continue

        name = file_path.name
        # Match pattern: anything ending in _p\d+ .ext
        match = re.search(r"^(.*)_p(\d+)(\..*)$", name)

        if match:
            base_hash = match.group(1)
            page_num = match.group(2)
            ext = match.group(3)

            # Check if it already starts with p\d+_
            if re.match(r"^p\d+_", name):
                print(f"Skipping {name}, already renamed.")
                continue

            new_name = f"p{page_num}_{base_hash}{ext}"
            new_path = images_dir / new_name

            print(f"Renaming {name} -> {new_name}")
            shutil.move(str(file_path), str(new_path))


if __name__ == "__main__":
    rename_files()
