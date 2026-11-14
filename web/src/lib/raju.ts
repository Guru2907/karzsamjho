import { useCallback, useSyncExternalStore } from 'react'

// Easy mode (Raju mode, E7): ONE shared setting that the top bar and every page read.
// - ?mode=raju (the website's QR) switches it on once; the parameter is then removed from the address,
//   so a later "off" sticks after a reload or when moving between pages.
// - Stored in localStorage ("ks-raju"); if storage is blocked it still works for this visit (memory).
// Fix (6:10 AM): the old hook dispatched a change event from inside a React state update, so the top bar
// and the page updated each other while rendering ("Cannot update a component while rendering a
// different component") and the switch did nothing.

const STORAGE_KEY = 'ks-raju'
const listeners = new Set<() => void>()
let memory = false

function read(): boolean {
  try {
    const v = localStorage.getItem(STORAGE_KEY)
    return v === null ? memory : v === 'true'
  } catch {
    return memory
  }
}

function write(on: boolean): void {
  memory = on
  try {
    localStorage.setItem(STORAGE_KEY, String(on))
  } catch {
    /* private mode: memory only */
  }
  listeners.forEach((l) => l())
}

function applyQrParam(): void {
  if (typeof window === 'undefined') return
  const url = new URL(window.location.href)
  if (url.searchParams.get('mode') !== 'raju') return
  write(true)
  url.searchParams.delete('mode')
  window.history.replaceState(window.history.state, '', url.pathname + url.search + url.hash)
}
applyQrParam()

function subscribe(listener: () => void): () => void {
  listeners.add(listener)
  window.addEventListener('storage', listener) // another tab changed it
  return () => {
    listeners.delete(listener)
    window.removeEventListener('storage', listener)
  }
}

export function useRajuMode(): [boolean, (val: boolean | ((prev: boolean) => boolean)) => void] {
  const on = useSyncExternalStore(subscribe, read, () => false)
  const setOn = useCallback((val: boolean | ((prev: boolean) => boolean)) => {
    write(typeof val === 'function' ? val(read()) : val)
  }, [])
  return [on, setOn]
}
