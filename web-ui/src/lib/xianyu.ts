import { Capacitor, registerPlugin } from '@capacitor/core'
const ExternalItem = registerPlugin<{ open(options: { url: string }): Promise<void> }>('ExternalItem')
export async function openXianyu(url: string) {
  const target = new URL(url)
  if (target.protocol !== 'https:' || !['www.goofish.com', 'goofish.com'].includes(target.hostname)) throw new Error('Invalid Goofish item link')
  if (Capacitor.isNativePlatform()) await ExternalItem.open({ url: target.toString() })
  else window.open(target.toString(), '_blank', 'noopener,noreferrer')
}
