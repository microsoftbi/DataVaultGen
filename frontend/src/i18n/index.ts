import { createI18n } from 'vue-i18n'
import zhCN from './locales/zh-CN'
import en from './locales/en'

const saved = localStorage.getItem('locale')
const browserLang = navigator.language.startsWith('zh') ? 'zh-CN' : 'en'
const defaultLocale = saved || browserLang

export const i18n = createI18n({
  legacy: false,
  locale: defaultLocale,
  fallbackLocale: 'en',
  messages: { 'zh-CN': zhCN, en },
})

export function setLocale(locale: string) {
  ;(i18n.global.locale as any).value = locale
  localStorage.setItem('locale', locale)
  document.documentElement.lang = locale
}
