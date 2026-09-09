// ── Holdings ──────────────────────────────────────────────────────────────────

export interface Holding {
  tradingsymbol: string
  exchange: string
  isin: string
  quantity: number
  average_price: number
  last_price: number
  pnl: number
  day_change: number
  day_change_percentage: number
  sector: string
  cap_category: string
  pe_ratio?: number
  pb_ratio?: number
  roe?: number
  div_yield?: number
  trend_200_sma?: string
  invested_value?: number
  current_value?: number
  pnl_percentage?: number
  weight_pct?: number
}

export interface PortfolioSummary {
  total_holdings_count: number
  total_investment: number
  current_value: number
  total_pnl: number
  total_pnl_percentage: number
}

export interface HoldingsResponse {
  status: string
  is_live: boolean
  error_message: string | null
  summary: PortfolioSummary
  holdings: Holding[]
}

// ── Performance ───────────────────────────────────────────────────────────────

export interface PerformanceMetrics {
  xirr_percentage: number
  sharpe_ratio: number
  sortino_ratio: number
  portfolio_beta: number
  weighted_pe: number
  weighted_roe: number
  herfindahl_index: number
  risk_profile_tag: string
}

export interface PerformanceResponse {
  status: string
  metrics: PerformanceMetrics
}

// ── Tax ───────────────────────────────────────────────────────────────────────

export interface TaxCandidate {
  tradingsymbol: string
  unrealized_loss: number
  holding_period_days: number
  tax_type: string
}

export interface TaxAnalysis {
  net_stcg: number
  stcg_tax_payable: number
  net_ltcg: number
  ltcg_tax_payable: number
  ltcg_exemption_used: number
  harvestable_loss_candidates: TaxCandidate[]
}

export interface TaxResponse {
  status: string
  tax_analysis: TaxAnalysis
}

// ── Margins ───────────────────────────────────────────────────────────────────

export interface MarginsEquity {
  enabled: boolean
  net: number
  available: { cash: number; opening_balance: number; live_balance: number; collateral: number }
}

export interface MarginsResponse {
  status: string
  margins: { equity: MarginsEquity }
}

// ── Advisory ──────────────────────────────────────────────────────────────────

export type AdvisoryAction = 'BUY' | 'SELL' | 'HOLD' | 'TRIM'

export interface Recommendation {
  symbol: string
  action: AdvisoryAction
  target_allocation_pct: number
  confidence_score: number
  rationale: string
  source: string
}

export interface RuleFlag {
  rule: string
  detail: string
  severity: 'HIGH' | 'MEDIUM' | 'LOW'
}

export interface AdvisoryResponse {
  status: string
  source: 'llm' | 'rule_engine'
  llm_provider?: string
  investment_goal: string
  rule_flags: RuleFlag[]
  recommendations: Recommendation[]
}

export interface BasketItem {
  symbol: string
  action: 'BUY' | 'SELL' | 'TRIM'
  quantity: number
  estimated_value: number
  reason: string
}

export interface BasketResponse {
  status: string
  basket: BasketItem[]
  total_buy_value: number
  total_sell_value: number
  budget_utilised_pct: number
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export interface LoginUrlResponse {
  status: string
  login_url: string
}

// ── Misc ──────────────────────────────────────────────────────────────────────

export type ConnectionMode = 'demo' | 'enctoken' | 'kite'
