"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const {calc, parseCsv, processCsv} = require("./app.js");
test("TMB low/threshold/very high", () => {
  assert.equal(calc(50, 38, 0).tmb, 1.32);
  assert.equal(calc(380, 38, 0).category, "High");
  assert.equal(calc(760, 38, 0).category, "Very high");
  assert.equal(calc(100, 38, 20).nonSynonymous, 80);
});
test("cutoff compares raw value rather than rounded display", () => {
  const result = calc(10, 1.00009, 0);
  assert.equal(result.tmb, 10);
  assert.equal(result.cutoff, false);
  assert.equal(result.category, "Intermediate");
});
test("rejects invalid numeric inputs", () => {
  assert.throws(() => calc(-1, 38, 0));
  assert.throws(() => calc(10.1, 38, 0));
  assert.throws(() => calc(10, Infinity, 0));
  assert.throws(() => calc(10, 0, 0));
  assert.throws(() => calc(10, 1, 11));
});
test("RFC4180 quotes, escaped quotes, CRLF and UTF-8 BOM", () => {
  const csv = "\uFEFFtotal_mutations,coding_region_size_mb,comment\r\n10,1,\"a,b\"\r\n20,2,\"say \"\"yes\"\"\"";
  const out = processCsv(csv);
  assert.equal(out.count, 2);
  assert.match(out.csv, /"a,b"/);
  assert.match(out.csv, /"say ""yes"""/);
  assert.equal(parseCsv(out.csv).length, 3);
});
test("rejects malformed CSV and spreadsheet formulas are sanitized", () => {
  assert.throws(() => processCsv("wrong,header\n1,2"));
  assert.throws(() => processCsv("total_mutations,coding_region_size_mb\n10,NaN"));
  assert.throws(() => processCsv("total_mutations,coding_region_size_mb\n10"));
  assert.throws(() => parseCsv('"unfinished'));
  const out = processCsv('total_mutations,coding_region_size_mb,note\n10,1,"=1+1"');
  assert.match(out.csv, /"'=1\+1"/);
});
