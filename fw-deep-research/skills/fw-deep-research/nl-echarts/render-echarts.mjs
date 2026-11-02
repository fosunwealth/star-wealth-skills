#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const SKILL_ROOT = path.resolve(__dirname, '..');
function parseArgs(argv) {
 const args = {input: null, out: null, width: 900, height: 520};
 for (let i = 2; i < argv.length; i++) {
  const a = argv[i];
  if (a === '--input' || a === '-i') args.input = argv[++i];
  else if (a === '--out' || a === '-o') args.out = argv[++i];
  else if (a === '--format' || a === '-f') {
   const format = String(argv[++i] || '').toLowerCase();
   if (format && format !== 'html') throw new Error('Only --format html is supported');
  } else if (a === '--width') args.width = Number(argv[++i]);
  else if (a === '--height') args.height = Number(argv[++i]);
  else if (a === '--help' || a === '-h') args.help = true;
 }
 return args;
}
function findLocalEchartsMinJs() {
 if (process.env.ECHARTS_JS) {
  const p = path.resolve(process.env.ECHARTS_JS);
  if (fs.existsSync(p) && fs.statSync(p).isFile()) return p;
  throw new Error(`ECHARTS_JS not found: ${p}`);
 }
 const candidates = [
  path.join(SKILL_ROOT, 'node_modules', 'echarts', 'dist', 'echarts.min.js'),
  path.join(SKILL_ROOT, 'node_modules', 'echarts', 'dist', 'echarts.js')
 ];
 try {
  const distDir = path.join(path.dirname(require.resolve('echarts/package.json', {paths: [SKILL_ROOT, __dirname]})), 'dist');
  candidates.push(path.join(distDir, 'echarts.min.js'), path.join(distDir, 'echarts.js'));
 } catch {}
 for (const p of candidates) if (fs.existsSync(p) && fs.statSync(p).isFile()) return p;
 return null;
}
function vendorEchartsNextToOut(outPath) {
 const src = findLocalEchartsMinJs();
 if (!src) throw new Error('Local echarts.min.js not found. Run npm install in the skill root.');
 const outDir = path.dirname(path.resolve(outPath));
 fs.mkdirSync(outDir, {recursive: true});
 const dest = path.join(outDir, 'echarts.min.js');
 if (!fs.existsSync(dest) || fs.statSync(dest).size !== fs.statSync(src).size) fs.copyFileSync(src, dest);
 return './echarts.min.js';
}
function unescapeEchartsText(value) {
 if (typeof value === 'string') {
  if (value.includes('\\n') || value.includes('\\t') || value.includes('\\r')) return value.replaceAll('\\r\\n', '\n').replaceAll('\\n', '\n').replaceAll('\\t', '\t').replaceAll('\\r', '\r');
  return value;
 }
 if (Array.isArray(value)) return value.map(unescapeEchartsText);
 if (value && typeof value === 'object') {
  const out = {};
  for (const [k, v] of Object.entries(value)) out[k] = unescapeEchartsText(v);
  return out;
 }
 return value;
}
function cleanHtmlTitle(title) {
 return Array.from(String(title || 'ECharts')).filter((char) => !'<>&'.includes(char)).join('');
}
function wrapInteractiveHtml(option, title, scriptSrc, width, height) {
 const source = String(scriptSrc).toLowerCase();
 if (source.startsWith('http://') || source.startsWith('https://') || source.includes('cdn.') || source.includes('jsdelivr') || source.includes('unpkg')) throw new Error(`External CDN script src is rejected: ${scriptSrc}`);
 const optionJson = JSON.stringify(option);
 return `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>${cleanHtmlTitle(title)}</title>
<script src="${scriptSrc}"></script>
<style>
html, body { margin: 0; height: 100%; background: #fff; }
#main { width: 100%; height: ${height}px; min-height: 420px; }
</style>
</head>
<body>
<div id="main"></div>
<script>
var option = ${optionJson};
var chart = echarts.init(document.getElementById('main'), null, {width: ${width}, height: ${height}});
chart.setOption(option);
window.addEventListener('resize', function () { chart.resize(); });
</script>
</body>
</html>
`;
}
async function main() {
 const args = parseArgs(process.argv);
 if (args.help || !args.input || !args.out) {
  console.log('Usage: node nl-echarts/render-echarts.mjs --input option.json --out chart.html --format html');
  process.exit(args.help ? 0 : 1);
 }
 const inputPath = path.resolve(args.input);
 const outPath = path.resolve(args.out);
 if (!fs.existsSync(inputPath)) throw new Error(`Input not found: ${inputPath}`);
 const option = unescapeEchartsText(JSON.parse(fs.readFileSync(inputPath, 'utf8')));
 fs.mkdirSync(path.dirname(outPath), {recursive: true});
 const scriptSrc = vendorEchartsNextToOut(outPath);
 const html = wrapInteractiveHtml(option, option?.title?.text || 'ECharts Chart', scriptSrc, args.width, args.height);
 fs.writeFileSync(outPath, html, 'utf8');
 console.log(JSON.stringify({ok: true, format: 'html', interactive: true, out: outPath, scriptSrc, bytes: fs.statSync(outPath).size}));
}
main().catch((err) => {
 console.error(String(err && err.stack || err));
 process.exit(1);
});
