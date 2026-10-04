// Include upstream and dependency license notices inside the APK's bundled assets.
import fs from 'node:fs'
import path from 'node:path'
import { execFileSync } from 'node:child_process'
const root = process.cwd()
const directories = execFileSync(process.platform === 'win32' ? 'npm.cmd' : 'npm', ['ls', '--all', '--parseable'], { encoding: 'utf8', shell: process.platform === 'win32' }).trim().split(/\r?\n/).sort()
const notices = [fs.readFileSync(path.join(root, '../LICENSE'), 'utf8'), fs.readFileSync(path.join(root, '../UPSTREAM.md'), 'utf8')]
for (const directory of directories) {
  const metadata = path.join(directory, 'package.json')
  if (!fs.existsSync(metadata)) continue
  const pkg = JSON.parse(fs.readFileSync(metadata, 'utf8'))
  for (const filename of fs.readdirSync(directory).sort()) {
    if (!/^(license|licence|copying|notice)(\.|$)/i.test(filename)) continue
    const source = path.join(directory, filename)
    if (fs.statSync(source).isFile()) notices.push(`\n--- ${pkg.name}@${pkg.version}: ${filename} ---\n${fs.readFileSync(source, 'utf8')}`)
  }
}
fs.mkdirSync(path.join(root, 'public'), { recursive: true })
fs.writeFileSync(path.join(root, 'public/THIRD_PARTY_NOTICES.txt'), notices.join('\n\n'), 'utf8')
