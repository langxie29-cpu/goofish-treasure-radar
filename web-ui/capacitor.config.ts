import type { CapacitorConfig } from '@capacitor/cli'
const config: CapacitorConfig = {
  appId: 'com.langxie.treasureradar',
  appName: 'Treasure Radar',
  webDir: '../dist',
  server: { androidScheme: 'https' },
  plugins: { CapacitorHttp: { enabled: true } },
}
export default config
