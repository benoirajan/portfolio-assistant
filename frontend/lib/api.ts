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
  MultiStagePipelineResponse,
  AuthResponse,
  MeResponse,
  BrokerStatusResponse,
} from './types'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000'

export const apiClient = axios.create({ baseURL: BASE_URL })

// Injects JWT Bearer token and optional X-Enctoken to all requests
apiClient.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const authToken = localStorage.getItem('auth_token')
    if (authToken) {
      config.headers['Authorization'] = `Bearer ${authToken}`
    }
    const enctoken = localStorage.getItem('enctoken')
    if (enctoken) {
      config.headers['X-Enctoken'] = enctoken
    }
  }
  return config
})

// Handle 401 Unauthorized responses
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      // Clear expired auth token
      localStorage.removeItem('auth_token')
      window.dispatchEvent(new Event('auth:unauthorized'))
    }
    return Promise.reject(error)
  }
)

// ── Authentication Endpoints ──────────────────────────────────────────────────

export const loginWithGoogle = (credential: string): Promise<AuthResponse> =>
  apiClient.post('/api/v1/auth/google', { credential }).then((r) => r.data)

export const loginWithEmail = (email: string, password: string): Promise<AuthResponse> =>
  apiClient.post('/api/v1/auth/login', { email, password }).then((r) => r.data)

export const registerUser = (
  email: string,
  password: string,
  full_name?: string
): Promise<AuthResponse> =>
  apiClient.post('/api/v1/auth/register', { email, password, full_name }).then((r) => r.data)

export const fetchCurrentUser = (): Promise<MeResponse> =>
  apiClient.get('/api/v1/auth/me').then((r) => r.data)

export const saveBrokerEnctoken = (enctoken: string): Promise<BrokerStatusResponse> =>
  apiClient.post('/api/v1/auth/broker/enctoken', { enctoken }).then((r) => r.data)

export const fetchBrokerStatus = (): Promise<BrokerStatusResponse> =>
  apiClient.get('/api/v1/auth/broker/status').then((r) => r.data)

export const disconnectBroker = (): Promise<{ status: string; message: string }> =>
  apiClient.delete('/api/v1/auth/broker/disconnect').then((r) => r.data)

// ── Portfolio & Analytics Endpoints ──────────────────────────────────────────

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

export const fetchMultiStagePipeline = (params: {
  total_budget: number
  monthly_capacity: number
  investment_schedule: string
  investment_goal: string
  allow_new_stocks: boolean
  max_single_stock_pct?: number
  max_sector_pct?: number
}): Promise<MultiStagePipelineResponse> =>
  apiClient.get('/api/v1/advisory/pipeline', { params }).then((r) => r.data)

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

export const invalidatePortfolioCache = (): Promise<{ status: string; keys_deleted: number }> =>
  apiClient.delete('/api/v1/cache/invalidate').then((r) => r.data)
