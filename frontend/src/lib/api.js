import { supabase } from './supabase'

export async function fetchWithAuth(url, options = {}) {
  const { data: { session } } = await supabase.auth.getSession()
  
  const headers = {
    ...options.headers,
  }

  if (session?.access_token) {
    headers['Authorization'] = `Bearer ${session.access_token}`
  }

  const shopId = localStorage.getItem('maruthi_active_shop') || 'shop_001'
  headers['X-Shop-ID'] = shopId

  return fetch(url, {
    ...options,
    headers,
  })
}
