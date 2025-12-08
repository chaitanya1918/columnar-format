import struct

MAGIC = b"CCF1"
VERSION = 1

COL_TYPE_INT32 = 0


def write_two_columns(path: str):
    # Data
    columns = [
        ("age", COL_TYPE_INT32, [10, 20, 30]),
        ("salary", COL_TYPE_INT32, [5000, 6000, 7000])
    ]

    num_columns = len(columns)
    num_rows = len(columns[0][2])

    with open(path, "wb") as f:
        # --- File identity ---
        f.write(MAGIC)
        f.write(struct.pack("<H", VERSION))

        # --- Header main values ---
        f.write(struct.pack("<H", num_columns))
        f.write(struct.pack("<I", num_rows))

        # Temporary metadata storage for offsets
        offsets_positions = []

        # --- Write metadata for each column ---
        for name, col_type, values in columns:
            f.write(struct.pack("<B", col_type))  # column type

            name_bytes = name.encode("utf-8")
            f.write(struct.pack("<B", len(name_bytes)))  # length
            f.write(name_bytes)  # name

            # Reserve space for offset (we will rewrite later)
            offsets_positions.append((f.tell(), values))
            f.write(b'\x00' * 8)  # placeholder

        # --- Write column data and fill offsets ---
        for offset_pos, (_, _, values) in zip(offsets_positions, columns):
            pos, values = offset_pos
            data_start = f.tell()

            # Write the actual data
            for v in values:
                f.write(struct.pack("<i", v))

            # Go back and write the correct offset
            current_pos = f.tell()
            f.seek(pos)
            f.write(struct.pack("<Q", data_start))
            f.seek(current_pos)

    print("File written with 2 columns successfully.")


if __name__ == "__main__":
    write_two_columns("example.ccf")
