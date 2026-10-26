# Retail data dictionary

Current source: UCI Online Retail by Chen, D. (2015), DOI:10.24432/C5BW33, CC BY 4.0. Source licence verified 26 October 2026. Full pipeline policies and integration schema are in RETAIL-DATA-CONTRACT.md. Earlier rental-data dictionary is preserved as DATA-DICTIONARY-BIKE.md.

| Source field | Meaning | Treatment |
| --- | --- | --- |
| InvoiceNo | Invoice identifier; C prefix indicates cancellation | Cancellation filter; training invoice coverage for SKU selection; not model feature |
| StockCode | Product identifier | String product_id; select five using training-only coverage |
| Description | Product name | Catalog/labels; nonempty requirement; not model text feature |
| Quantity | Units on a transaction line | Positive gross sales aggregated by product/date; negative returns excluded and audited |
| InvoiceDate | Invoice timestamp, source does not encode timezone offset | Normalize to local calendar day; exclude last partial source day |
| UnitPrice | Price in sterling | Require positive; not a future feature |
| CustomerID | Customer identifier | Unused; never retained in derived outputs |
| Country | Customer country | UK scope filter; not a store/location identifier |

Derived columns: date, product_id, units (nonnegative recorded gross sales), has_recorded_sale. Absence of sales records is zero recorded sales only; missing extraction, closure and stockouts remain indistinguishable. Full counts/actual nulls are in reports/retail/quality.json. Forecast features and cutoffs are documented in the contract. Stock, supplier lead time, promotions and stockout flags are not available.
