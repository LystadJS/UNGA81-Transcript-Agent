const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '../..');
require('esbuild').buildSync({
  entryPoints: [path.join(__dirname, 'entry.js')], bundle: true,
  outfile: path.join(root, 'site/numerics.js'), format: 'iife',
  globalName: 'UNNumerics', platform: 'browser', target: 'es2020', minify: true,
  legalComments: 'inline',
  footer: { js: 'if(typeof module!=="undefined"&&module.exports)module.exports=UNNumerics;' }
});
const lock = require('./package-lock.json');
const notices = [], packages = [];
for (const [location, info] of Object.entries(lock.packages)) {
  if (!location || info.dev || info.optional) continue;
  const dir = path.join(__dirname, location);
  const meta = JSON.parse(fs.readFileSync(path.join(dir, 'package.json'), 'utf8'));
  const licenseFile = fs.readdirSync(dir).find(f => /^licen[sc]e(?:\.|$)/i.test(f));
  if (!licenseFile) throw Error('Missing license for '+location);
  notices.push(`${meta.name} ${meta.version}\n${meta.repository?.url || meta.repository || ''}\n${fs.readFileSync(path.join(dir, licenseFile), 'utf8')}`);
  packages.push({name: meta.name, version: meta.version, integrity: info.integrity});
}
fs.writeFileSync(path.join(root, 'site/NUMERICS_LICENSES.txt'), notices.join('\n\n==========\n\n'));
fs.writeFileSync(path.join(root, 'site/numerics-manifest.json'), JSON.stringify({
  packages, sha256: crypto.createHash('sha256').update(fs.readFileSync(path.join(root, 'site/numerics.js'))).digest('hex')
}, null, 2)+'\n');
console.log('Built local numerical bundle with dependency licenses and hash.');
