// The package root is "type": "module", so Node would parse dist/cjs/*.js as ESM.
// A nested package.json marks the CommonJS build as CommonJS.
import { writeFileSync } from 'node:fs';

writeFileSync(new URL('../dist/cjs/package.json', import.meta.url), '{ "type": "commonjs" }\n');
