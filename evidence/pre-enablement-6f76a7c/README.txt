Historical disabled-gate source and test evidence, copied byte-for-byte from
merged SDK 6f76a7c605014b2ce13c76e6884f22bbf53094df. SHA256.json records the bytes.

These historical files are outside current tests/ collection. They demonstrate
the formerly disabled default and test-only enabling override. Do not rewrite
them to pass the enabled candidate. Current tests preserve closed-gate safety
explicitly and exercise the candidate's normal public API without enabling patches.
