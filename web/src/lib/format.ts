// Formatting helpers and error messages for KarzSamjho.

export const ERROR_MESSAGES = {
  SERVER_OFF: 'Server se baat nahi ho pa rahi. Thodi der baad dobara try karo.',
  TIMEOUT: 'Bahut der lag rahi hai. Dobara bhejo.',
} as const

export function rupees(n: number | null | undefined): string {
  if (n == null || isNaN(n)) return '₹0'
  const formatted = new Intl.NumberFormat('en-IN', {
    maximumFractionDigits: 0,
  }).format(Math.round(n))
  return `₹${formatted}`
}

export function days(n: number | null | undefined): string {
  if (n == null || isNaN(n)) return '0 days'
  return `${n} days`
}
