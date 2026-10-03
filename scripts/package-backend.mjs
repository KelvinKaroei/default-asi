import { cpSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
const root = fileURLToPath(new URL('../', import.meta.url));
const result = spawnSync(
  resolve(root, '.venv/Scripts/python.exe'),
  [
    '-m',
    'PyInstaller',
    '--noconfirm',
    '--onedir',
    '--console',
    '--name',
    'cyber-backend',
    '--distpath',
    'build/sidecar',
    '--workpath',
    'build/pyinstaller',
    '--specpath',
    'build',
    '--paths',
    'backend',
    '--collect-all',
    'faiss',
    '--collect-all',
    'uvicorn',
    '--add-data',
    `${resolve(root, 'backend/assets')};assets`,
    '--hidden-import',
    'app.extract_material',
    'backend/launcher.py',
  ],
  { cwd: root, stdio: 'inherit', shell: false },
);
process.exitCode = result.status ?? 1;

if (result.status === 0)
  cpSync(resolve(root, '.tools/ollama'), resolve(root, 'build/ollama-package'), {
    recursive: true,
    filter: (source) => !source.split(/[\\/]/).includes('cuda_v13'),
  });
