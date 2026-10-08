'use strict';

// Reproducibly materialize the fictional evidence report used by viewer.html.
// Example: node research/supervised_country_positions/build_synthetic.cjs /tmp/positions-demo.json
const fs = require('node:fs');
const path = require('node:path');
const { makeSyntheticFrame } = require('./synthetic_fixture.cjs');
const { summarize, validateReport } = require('./position_core.cjs');

const output = process.argv[2];
if (!output) {
  process.stderr.write('Usage: node build_synthetic.cjs OUTPUT.json (new file)\n');
  process.exit(2);
}
const target = path.resolve(output);
if (fs.existsSync(target)) {
  process.stderr.write('Refusing to overwrite: ' + target + '\n');
  process.exit(2);
}
const book = JSON.parse(fs.readFileSync(path.join(__dirname, 'propositions.v1.json'), 'utf8'));
const input = makeSyntheticFrame(book);
const report = summarize(input, book);
validateReport(report);
fs.mkdirSync(path.dirname(target), { recursive: true });
fs.writeFileSync(target, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
process.stdout.write('Fictional report created: ' + target + '\n' +
  'Dataset: synthetic_engineering; model_fitted=false; publication_eligible=false\n' +
  'Profiles: ' + report.profiles.length + '; pairs: ' + report.edges.length +
  '; evidence: ' + report.evidence.length + '\n');
