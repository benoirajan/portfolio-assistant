import { useQuery } from '@tanstack/react-query'
import {
  fetchHoldings,
  fetchPerformance,
  fetchTax,
  fetchMargins,
  fetchAdvisory,
} from '@/lib/api'

const STALE = 5 * 60 * 1000

export const useHoldings = () =>
  useQuery({ queryKey: ['holdings'], queryFn: fetchHoldings, staleTime: STALE })

export const usePerformance = () =>
  useQuery({ queryKey: ['performance'], queryFn: fetchPerformance, staleTime: STALE })

export const useTax = () =>
  useQuery({ queryKey: ['tax'], queryFn: fetchTax, staleTime: STALE })

export const useMargins = () =>
  useQuery({ queryKey: ['margins'], queryFn: fetchMargins, staleTime: STALE })

export const useAdvisory = (goal: string, maxStock: number, maxSector: number) =>
  useQuery({
    queryKey: ['advisory', goal, maxStock, maxSector],
    queryFn: () => fetchAdvisory(goal, maxStock, maxSector),
    staleTime: STALE,
  })
