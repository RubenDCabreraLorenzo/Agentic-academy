# Legal and publisher files

Only the owner supplies these files. Do not generate, infer or draft their contents.

**`privacy.md` and `terms.md` currently hold lorem ipsum, at the owner's request. Replace it with the real text before public launch.**

| File | Effect when present | When absent |
|------|---------------------|-------------|
| `privacy.md` | `/privacy` renders it; links appear in the footers and on `/register` | Not found; links hidden |
| `terms.md` | `/terms` renders it; links appear in the footers and on `/register` | Not found; links hidden |
| `publisher.json` | Publisher and contact details appear in the footers | Not shown |

`publisher.json` needs `name` and `contact_email`, and may have `address` and `registration`.

Public launch stays blocked until all three exist (spec SC-019). See the [public content contract](../../../../specs/002-premium-product-experience/contracts/public-content.md).
