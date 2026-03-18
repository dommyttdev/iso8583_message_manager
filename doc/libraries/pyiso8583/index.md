# Python ISO8583 Protocol Serializer & Deserializer

iso8583 is a Python package that serializes and deserializes ISO8583 data between a bytes or bytearray instance containing ISO8583 data and a Python dict.

## At a Glance

iso8583 package supports custom specifications. See [iso8583.specs](specifications.md) module.

Use [iso8583.decode()](functions.md#iso8583.decode(s,%20spec)) to decode raw iso8583 message.

```python
>>> import iso8583
>>> from iso8583.specs import default_ascii as spec
>>> encoded_raw = b'02004000000000000000101234567890'
>>> decoded, encoded = iso8583.decode(encoded_raw, spec)
```

Use [iso8583.encode()](functions.md#iso8583.encode(doc_dec,%20spec)) to encode updated ISO8583 message. It returns a raw ISO8583 message and a dictionary with encoded data.

```python
>>> import iso8583
>>> from iso8583.specs import default_ascii as spec
>>> decoded = {"t": "0200", "2": "1234567890", "39": "00"}
>>> encoded_raw, encoded = iso8583.encode(decoded, spec)
```

To install:
```bash
pip install pyiso8583
```

Table of Contents:
- [Intro](intro.md)
- [How-To](howto.md)
- [Specifications](specifications.md)
- [Functions](functions.md)
- [Change Log](changelog.md)
