# Functions

## Main Functions

### `iso8583.decode(s, spec)`

Deserialize a bytes or bytearray instance containing ISO8583 data to a Python dict.

**Parameters:**
- `s` (bytes or bytearray) – Encoded ISO8583 data
- `spec` (dict) – A Python dict defining ISO8583 specification. See [`iso8583.specs`](specifications.md) module for examples.

**Returns:**
- `doc_dec` (dict) – Dict containing decoded ISO8583 data
- `doc_enc` (dict) – Dict containing encoded ISO8583 data

**Raises:**
- `DecodeError` – An error decoding ISO8583 bytearray
- `TypeError` – `s` must be a bytes or bytearray instance

**Examples:**

```python
>>> import pprint
>>> import iso8583
>>> from iso8583.specs import default_ascii as spec
>>> s = b"02004010100000000000161234567890123456123456111"
>>> doc_dec, doc_enc = iso8583.decode(s, spec)
>>> pprint.pprint(doc_dec)
{'12': '123456',
 '2': '1234567890123456',
 '20': '111',
 'p': '4010100000000000',
 't': '0200'}
```

### `iso8583.encode(doc_dec, spec)`

Serialize Python dict containing ISO8583 data to a bytearray.

**Parameters:**
- `doc_dec` (dict) – Dict containing decoded ISO8583 data
- `spec` (dict) – A Python dict defining ISO8583 specification. See [`iso8583.specs`](specifications.md) module for examples.

**Returns:**
- `s` (bytearray) – Encoded ISO8583 data
- `doc_enc` (dict) – Dict containing encoded ISO8583 data

**Raises:**
- `EncodeError` – An error encoding ISO8583 bytearray
- `TypeError` – `doc_dec` must be a dict instance

**Examples:**

```python
>>> import iso8583
>>> from iso8583.specs import default_ascii as spec
>>> doc_dec = {
...     't': '0210',
...     '3': '111111',
...     '39': '05'}
>>> s, doc_enc = iso8583.encode(doc_dec, spec)
>>> s
bytearray(b'0210200000000200000011111105')
```

## Exceptions

### `iso8583.DecodeError`

Subclass of `ValueError` that describes ISO8583 decoding error.

- `msg` (str) – The unformatted error message
- `s` (bytes or bytearray) – The ISO8583 bytes instance being parsed
- `doc_dec` (dict) – Dict containing partially decoded ISO8583 data
- `doc_enc` (dict) – Dict containing partially encoded ISO8583 data
- `pos` (int) – The start index where ISO8583 bytes data failed parsing
- `field` (str) – The ISO8583 field where parsing failed

### `iso8583.EncodeError`

Subclass of `ValueError` that describes ISO8583 encoding error.

- `msg` (str) – The unformatted error message
- `doc_dec` (dict) – Dict containing decoded ISO8583 data being encoded
- `doc_enc` (dict) – Dict containing partially encoded ISO8583 data
- `field` (str) – The ISO8583 field where parsing failed

## Helper Functions

### `iso8583.pp(doc, spec, desc_width=30, stream=None, line_width=80)`

Pretty Print Python dict containing ISO8583 data.

**Parameters:**
- `doc` (dict) – Dict containing ISO8583 data
- `spec` (dict) – A Python dict defining ISO8583 specification. See [`iso8583.specs`](specifications.md) module for examples.
- `desc_width` (int, optional) – Field description width (default 30). Specify 0 to print no descriptions.
- `stream` (stream, optional) – An output stream. The only method used on the stream object is the file protocol’s `write()` method. If not specified, the `iso8583.pp()` adopts `sys.stdout`.
- `line_width` (int, optional) – Attempted maximum width of output line (default 80).

**Notes:**

For the most correct information to be displayed by `iso8583.pp()` it’s recommended to call it after `iso8583.encode()` or `iso8583.decode()`.

**Examples:**

```python
>>> import iso8583
>>> from iso8583.specs import default_ascii as spec
>>> s = b"02004010100000000000161234567890123456123456840"
>>> doc_dec, doc_enc = iso8583.decode(s, spec)
>>> iso8583.pp(doc_dec, spec)
t   Message Type                           : '0200'
p   Bitmap, Primary                        : '4010100000000000'
2   Primary Account Number (PAN)           : '1234567890123456'
12  Time, Local Transaction                : '123456'
20  PAN Country Code                       : '840'
```
