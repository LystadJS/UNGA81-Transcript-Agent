'use strict';
const assert = require('node:assert/strict');
const Dates = require('../site/reporting-date.js');
const checks = [
  ['2026-11-05T04:59:59Z', '2026-11-04'],
  ['2026-11-05T05:00:00Z', '2026-11-05'],
  ['2026-07-05T03:59:59Z', '2026-07-04'],
  ['2026-07-05T04:00:00Z', '2026-07-05'],
  ['2026-03-08T06:59:59Z', '2026-03-08'],
  ['2026-03-08T07:00:00Z', '2026-03-08'],
  ['2026-11-01T05:30:00Z', '2026-11-01'],
  ['2026-11-01T06:30:00Z', '2026-11-01'],
  ['2027-01-01T04:59:59Z', '2026-12-31']
];
for (const [instant, expected] of checks) assert.equal(Dates.today(instant), expected);
assert.deepEqual(Dates.range('today', '2026-11-05T04:59:59Z'), {start:'2026-11-04',end:'2026-11-04'});
assert.deepEqual(Dates.range('yesterday', '2026-03-09T04:01:00Z'), {start:'2026-03-08',end:'2026-03-08'});
assert.deepEqual(Dates.range('yesterday', '2026-11-02T05:01:00Z'), {start:'2026-11-01',end:'2026-11-01'});
assert.deepEqual(Dates.range('week', '2027-01-01T05:00:00Z'), {start:'2026-12-26',end:'2027-01-01'});
assert.equal(Dates.shift('2024-03-01', -1), '2024-02-29');
assert.throws(() => Dates.shift('2026-02-30', -1));
assert.throws(() => Dates.shift('2026-01-01', 0.5));
assert.throws(() => Dates.today('invalid'));
assert.throws(() => Dates.range('unsupported'));
console.log('PASS New York reporting dates: midnight, DST, year boundaries and invalid inputs');
