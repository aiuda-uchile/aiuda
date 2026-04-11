import translations from "./translations.json"
import { useState } from "react"

let currentLang = "es"

export function setLanguage(lang) {
  currentLang = lang
}

export function t(key) {
  return translations[currentLang]?.[key] || key
}

export function useI18n() {
  const [lang, setLang] = useState(currentLang)

  const changeLanguage = (newLang) => {
    setLanguage(newLang)
    setLang(newLang)
  }

  return {
    t,
    lang,
    changeLanguage,
  }
}