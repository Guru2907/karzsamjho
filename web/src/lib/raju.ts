import { useState, useCallback } from 'react'

const STORAGE_KEY = 'ks-raju'

export function useRajuMode(): [boolean, (val: boolean | ((prev: boolean) => boolean)) => void] {
  const [on, setOnState] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false
    try {
      const params = new URLSearchParams(window.location.search)
      if (params.get('mode') === 'raju') {
        localStorage.setItem(STORAGE_KEY, 'true')
        return true
      }
      return localStorage.getItem(STORAGE_KEY) === 'true'
    } catch {
      return false
    }
  })

  const setOn = useCallback((val: boolean | ((prev: boolean) => boolean)) => {
    setOnState((prev) => {
      const next = typeof val === 'function' ? val(prev) : val
      try {
        localStorage.setItem(STORAGE_KEY, String(next))
      } catch {}
      return next
    })
  }, [])

  return [on, setOn]
}
