import struct
MAGIC = b"CCF1"
COL_TYPE_INT32 = 0  
def read_ccf(path: str):
    with open(path, "rb") as f:
        # 1) Magic
        magic = f.read(4)
        if magic != MAGIC:
            print("Not a CCF file! Magic mismatch:", magic)
            return

        # 2) Version
        (version,) = struct.unpack("<H", f.read(2))

        # 3) Number of columns and rows
        (num_cols,) = struct.unpack("<H", f.read(2))
        (num_rows,) = struct.unpack("<I", f.read(4))

        print("Magic      :", magic)
        print("Version    :", version)
        print("Num cols   :", num_cols)
        print("Num rows   :", num_rows)
        print()

        # 4) Read column metadata
        columns = []
        for i in range(num_cols):
            (col_type,) = struct.unpack("<B", f.read(1))
            (name_len,) = struct.unpack("<B", f.read(1))
            name_bytes = f.read(name_len)
            name = name_bytes.decode("utf-8")
            (offset,) = struct.unpack("<Q", f.read(8))

            columns.append((col_type, name, offset))

        # Print column info
        for i, (col_type, name, offset) in enumerate(columns):
            print(f"Column {i}:")
            print("  Name :", name)
            print("  Type :", col_type)
            print("  Offset:", offset)
        print()

        # 5) Read and print data for each column
        for col_type, name, offset in columns:
            print(f"Data for column '{name}':")
            f.seek(offset)

            if col_type == COL_TYPE_INT32:
                values = []
                for _ in range(num_rows):
                    (v,) = struct.unpack("<i", f.read(4))
                    values.append(v)
                print("  int32 values:", values)
            else:
                print("  (Unsupported column type in this simple reader.)")
            print()


if __name__ == "__main__":
    read_ccf("example.ccf")
