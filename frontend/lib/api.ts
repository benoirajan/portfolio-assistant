import axios from 'axios'
import type {
  HoldingsResponse,
  PerformanceResponse,
  TaxResponse,
  MarginsResponse,
  AdvisoryResponse,
  LoginUrlResponse,
  Recommendation,
  BasketResponse,
  ZerodhaBasket,
  ExportZerodhaBasketPayload,
  ExportZerodhaBasketResponse,
} from './types'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000'

export const apiClient = axios.create({ baseURL: BASE_URL })

apiClient.interceptors.request.use((config) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('enctoken') : null
  if (token) config.headers['X-Enctoken'] = token
  return config
})

export const fetchHoldings = (): Promise<HoldingsResponse> =>
  apiClient.get('/api/v1/holdings').then((r) => r.data)

export const fetchPerformance = (): Promise<PerformanceResponse> =>
  apiClient.get('/api/v1/analytics/performance').then((r) => r.data)

export const fetchTax = (): Promise<TaxResponse> =>
  apiClient.get('/api/v1/analytics/tax-harvesting').then((r) => r.data)

export const fetchMargins = (): Promise<MarginsResponse> =>
  apiClient.get('/api/v1/margins').then((r) => r.data)

export const fetchAdvisory = (
  goal: string,
  maxStock: number,
  maxSector: number
): Promise<AdvisoryResponse> =>
  apiClient
    .get('/api/v1/advisory/recommendations', {
      params: {
        investment_goal: goal,
        max_single_stock_pct: maxStock,
        max_sector_pct: maxSector,
      },
    })
    .then((r) => r.data)

export const fetchLoginUrl = (): Promise<LoginUrlResponse> =>
  apiClient.get('/api/v1/auth/login-url').then((r) => r.data)

export const checkHealth = (): Promise<boolean> =>
  apiClient
    .get('/health')
    .then(() => true)
    .catch(() => false)

export const createBasket = (
  recommendations: Recommendation[],
  max_budget: number
): Promise<BasketResponse> =>
  apiClient
    .post('/api/v1/advisory/basket', { recommendations, max_budget })
    .then((r) => r.data)

export const fetchZerodhaBaskets = (): Promise<{ status: string; baskets: ZerodhaBasket[]; error?: string }> =>
  apiClient.get('/api/v1/advisory/zerodha-baskets').then((r) => r.data)

export const exportZerodhaBasket = (
  payload: ExportZerodhaBasketPayload
): Promise<ExportZerodhaBasketResponse> =>
  apiClient.post('/api/v1/advisory/export-zerodha-basket', payload).then((r) => r.data)
