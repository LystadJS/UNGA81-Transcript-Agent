/* Calendar dates for the UN New York reporting day, independent of device timezone. */
(function(root) {
  'use strict';
  const TIME_ZONE = 'America/New_York';
  function today(now = new Date()) {
    const instant = now instanceof Date ? now : new Date(now);
    if (!Number.isFinite(instant.getTime())) throw Error('A valid reporting instant is required.');
    const parts = new Intl.DateTimeFormat('en-US', {
      timeZone: TIME_ZONE, year: 'numeric', month: '2-digit', day: '2-digit'
    }).formatToParts(instant);
    const value = type => parts.find(part => part.type === type).value;
    return `${value('year')}-${value('month')}-${value('day')}`;
  }
  function shift(day, delta) {
    if (typeof day !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(day) || !Number.isInteger(delta)) {
      throw Error('A valid calendar date and integer day offset are required.');
    }
    // Shift calendar labels rather than subtracting elapsed hours across DST changes.
    const date = new Date(day + 'T12:00:00Z');
    if (!Number.isFinite(date.getTime()) || date.toISOString().slice(0, 10) !== day) {
      throw Error('A valid calendar date is required.');
    }
    date.setUTCDate(date.getUTCDate() + delta);
    return date.toISOString().slice(0, 10);
  }
  function range(mode = 'today', now = new Date()) {
    const end = today(now);
    if (mode === 'today') return { start: end, end };
    if (mode === 'yesterday') { const day = shift(end, -1); return { start: day, end: day }; }
    if (mode === 'week') return { start: shift(end, -6), end };
    throw Error('Unsupported reporting-date shortcut.');
  }
  const api = { TIME_ZONE, today, shift, range };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.UNReportingDate = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
