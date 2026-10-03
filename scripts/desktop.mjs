import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { delimiter, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const env = { ...process.env };
const localCargo = resolve(root, '.tools/cargo');
if (existsSync(resolve(localCargo, 'bin/cargo.exe'))) {
  env.CARGO_HOME = localCargo;
  env.RUSTUP_HOME = resolve(root, '.tools/rustup');
  // No Windows, a chave costuma ser "Path". Evite criar uma segunda chave "PATH".
  const pathKey = Object.keys(env).find((key) => key.toLowerCase() === 'path') ?? 'PATH';
  env[pathKey] = `${resolve(localCargo, 'bin')}${delimiter}${env[pathKey] ?? ''}`;
}
const cli = resolve(root, 'node_modules/@tauri-apps/cli/tauri.js');
const child = spawn(process.execPath, [cli, ...process.argv.slice(2)], {
  cwd: resolve(root, 'desktop'),
  env,
  stdio: 'inherit',
  shell: false,
});
child.on('error', (error) => {
  console.error('Não foi possível iniciar o Tauri:', error.message);
  process.exitCode = 1;
});
child.on('exit', (code) => {
  process.exitCode = code ?? 1;
});
