# CCF: Custom Columnar Format (v1)

This document defines the binary structure of the CCF file format.

---

## 1. File Identity

Every CCF file starts with:

| Position | Size | Value | Meaning |
|----------|------|--------|---------|
| 0–3 | 4 bytes | "CCF1" | Magic text identifying the file format |
| 4–5 | 2 bytes | Version number (little-endian) | Current version: 1 |

Example beginning of file (hex):

43 43 46 31 01 00
 C  C  F  1  v1

---

## 2. Header Format

After the identity, the header describes the structure of the data.

| Field | Size | Type | Description |
|-------|------|------|-------------|
| Number of columns | 2 bytes | uint16 | Total number of columns |
| Number of rows | 4 bytes | uint32 | Number of rows in each column |

Then for each column:

| Field | Size | Type | Meaning |
|-------|------|------|---------|
| Column type | 1 byte | uint8 | 0 = int32, 1 = float64, 2 = string |
| Name length | 1 byte | uint8 | Length of column name |
| Column name | variable | UTF-8 string | The name of the column |
| Column data offset | 8 bytes | uint64 (little-endian) | File position where this column’s data begins |

---

## 3. Data Section

After the header, the actual values are stored column by column.

### 3.1 Fixed-Width Types

For numeric types (int32, float64), values are stored sequentially:

[row0][row1][row2]...[rowN]

Example sizes:

| Type | Bytes per value |
|------|-----------------|
| int32 | 4 bytes |
| float64 | 8 bytes |

---

### 3.2 String Data

Strings are stored as pairs:

[length][string_bytes][length][string_bytes]...

Where:

- `length` is a uint32 (little-endian)
- `string_bytes` is UTF-8 encoded text

Example ("hello", "ok") stored as:

05 00 00 00 68 65 6C 6C 6F  
02 00 00 00 6F 6B

---

## 4. Endianness

All numeric values are stored in **little-endian format**.

---

## 5. Validation Rules

A CCF file is valid only if:

- Magic bytes match `"CCF1"`
- Version is supported
- All column offsets point to valid data positions
- Row counts match expected sizes

If any condition fails, the reader must treat the file as corrupted.

---

## 6. Binary Data Handling

### 6.1 Creating the CCF file

To create a new CCF file (or overwrite an old one), the file is opened in
**write-binary mode**:

- In Python: `open(path, "wb")`
- If the file does not exist → it is created.
- If the file already exists → it is cleared (truncated to 0 bytes).

After opening in `"wb"` mode, the program writes the data in this order:

1. Magic bytes (`CCF1`)
2. Version number
3. Header (number of columns, number of rows, column metadata)
4. Column data blocks

This guarantees the file always has a valid CCF structure.

### 6.2 Clearing the file

To clear the file, we also open it with `"wb"`:

- Opening with `"wb"` removes all old contents.
- Then we can write a fresh header and data again.

So **"create" and "clear"** are done the same way: by opening with `"wb"` and then writing a new CCF header and data.

### 6.3 Reading binary data

To read an existing CCF file, it is opened in **read-binary mode**:

- In Python: `open(path, "rb")`

The program then:

1. Reads the first 4 bytes for the magic text.
2. Reads the version (2 bytes).
3. Reads number of columns and rows.
4. Reads column metadata to get each column’s offset.
5. Uses `seek(offset)` to jump to the column data and `read()` to load the values.

Numeric values are converted using `struct.unpack(...)`, and strings are read using their length followed by UTF-8 bytes.

---

## 7. Variable-Length String Encoding

Handling variable-length data such as strings is an important part of the design. Unlike integers or floats, strings do not all have the same size, so their positions in the file cannot be calculated using a simple fixed step. A common solution is to store string data in two parts: an index and a data block.

In this approach, all string characters are concatenated together into one continuous data block. Separately, another block stores the offsets or lengths for each string. Each offset tells the reader where a string starts (or ends) inside the concatenated block. When reading, the program first uses the index (offsets or lengths) to locate the boundaries of each string, and then reads the corresponding bytes from the data block.

This method is efficient because it avoids scanning the entire file to find individual strings and keeps the string data tightly packed in memory.

---
## 8. Testing and Validation

For testing and validation, I focused on checking that the CCF writer and reader behaved correctly with simple, controlled data.

First, I created a small test program (`writer.py`) that writes a file called `example.ccf` using the format defined in `SPEC.md`. The writer stores the magic bytes (`CCF1`), version number, header fields, and then column data. I started with one integer column (`age`) with a few sample values (10, 20, 30), and later extended the logic to support multiple columns.

Next, I implemented a separate program (`reader.py`) that opens the same `example.ccf` file and reads it back in binary mode. The reader checks the magic bytes and version, reads the number of columns and rows, parses the column metadata, and then uses the stored offsets to seek to the correct positions in the file and load the column data. For integer columns, the reader uses `struct.unpack` to convert the raw bytes back into Python integers.

To validate the implementation, I compared the values printed by `reader.py` with the original values passed into `writer.py`. For example, after writing the `age` column with values `[10, 20, 30]`, I confirmed that the reader printed the same list of values. This round-trip check (write → read → compare) gave me confidence that both the header and data sections were being written and interpreted correctly according to the specification.

I repeated the same process with two columns (`age` and `salary`) to confirm that multiple columns, their metadata, and their offsets were all handled correctly.
