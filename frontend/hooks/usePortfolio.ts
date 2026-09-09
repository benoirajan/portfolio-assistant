import { useQuery, useMutation } from '@tanstack/react-query'
import { useState, useEffect } from 'react'
import {
  fetchHoldings,
  fetchPerformance,
  fetchTax,
  fetchMargins,
  fetchAdvisory,
  createBasket,
} from '@/lib/api'
import type { Recommendation } from '@/lib/types'

const STALE = 5 * 60 * 1000

function useDebounce<T>(value: T, delay = 1000): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(t)
  }, [value, delay])
  return debounced
}

export const useHoldings = () =>
  useQuery({ queryKey: ['holdings'], queryFn: fetchHoldings, staleTime: STALE })

export const usePerformance = () =>
  useQuery({ queryKey: ['performance'], queryFn: fetchPerformance, staleTime: STALE })

export const useTax = () =>
  useQuery({ queryKey: ['tax'], queryFn: fetchTax, staleTime: STALE })

export const useMargins = () =>
  useQuery({ queryKey: ['margins'], queryFn: fetchMargins, staleTime: STALE })

export const useAdvisory = (goal: string, maxStock: number, maxSector: number) => {
  const debouncedStock = useDebounce(maxStock)
  const debouncedSector = useDebounce(maxSector)
  return useQuery({
    queryKey: ['advisory', goal, debouncedStock, debouncedSector],
    queryFn: () => fetchAdvisory(goal, debouncedStock, debouncedSector),
    staleTime: STALE,
  })
}

export const useBasket = () =>
  useMutation({
    mutationFn: ({ recommendations, budget }: { recommendations: Recommendation[]; budget: number }) =>
      createBasket(recommendations, budget),
  })
