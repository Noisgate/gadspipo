import useSWR from 'swr'
import { apiClient } from '@/lib/api-client'
import { Campaign, CampaignDetail, CampaignInvestigation, GoogleAdsCommandCenter } from '@/types'

export function useCampaigns() {
  const { data, error, isLoading, mutate } = useSWR<Campaign[]>(
    '/campaigns',
    () => apiClient.getCampaigns(),
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
      refreshInterval: 30000, // Revalidate every 30 seconds
    }
  )

  return {
    campaigns: data || [],
    isLoading,
    isError: !!error,
    error: error ? apiClient.getErrorMessage(error) : null,
    mutate,
  }
}

export function useCampaignDetail(campaignId: string | null) {
  const { data, error, isLoading, mutate } = useSWR<CampaignDetail>(
    campaignId ? `/campaigns/${campaignId}` : null,
    campaignId ? () => apiClient.getCampaignDetail(campaignId) : null,
    {
      revalidateOnFocus: false,
      refreshInterval: 30000,
    }
  )

  return {
    campaign: data,
    isLoading,
    isError: !!error,
    error: error ? apiClient.getErrorMessage(error) : null,
    mutate,
  }
}

export function useCampaignKeywords(campaignId: string | null) {
  const { data, error, isLoading, mutate } = useSWR(
    campaignId ? `/campaigns/${campaignId}/keywords` : null,
    campaignId ? () => apiClient.getCampaignKeywords(campaignId) : null,
    {
      revalidateOnFocus: false,
      refreshInterval: 60000,
    }
  )

  return {
    keywords: data || [],
    isLoading,
    isError: !!error,
    error: error ? apiClient.getErrorMessage(error) : null,
    mutate,
  }
}

export function useCampaignSearchTerms(campaignId: string | null) {
  const { data, error, isLoading, mutate } = useSWR(
    campaignId ? `/campaigns/${campaignId}/search-terms` : null,
    campaignId ? () => apiClient.getCampaignSearchTerms(campaignId) : null,
    {
      revalidateOnFocus: false,
      refreshInterval: 60000,
    }
  )

  return {
    searchTerms: data || [],
    isLoading,
    isError: !!error,
    error: error ? apiClient.getErrorMessage(error) : null,
    mutate,
  }
}

export function useCampaignInvestigation(campaignId: string | null) {
  const { data, error, isLoading, mutate } = useSWR<CampaignInvestigation | null>(
    campaignId ? `/campaigns/${campaignId}/investigation/latest` : null,
    campaignId ? () => apiClient.getLatestCampaignInvestigation(campaignId) : null,
    {
      revalidateOnFocus: false,
      refreshInterval: 30000,
    }
  )

  return {
    investigation: data || null,
    isLoading,
    isError: !!error,
    error: error ? apiClient.getErrorMessage(error) : null,
    mutate,
  }
}

export function useDashboardStats() {
  const { data, error, isLoading } = useSWR(
    '/campaigns/performance/dashboard',
    () => apiClient.getDashboardStats(),
    {
      revalidateOnFocus: false,
      refreshInterval: 30000,
    }
  )

  return {
    stats: data,
    isLoading,
    isError: !!error,
    error: error ? apiClient.getErrorMessage(error) : null,
  }
}

export function useGoogleAdsCommandCenter() {
  const { data, error, isLoading, mutate } = useSWR<GoogleAdsCommandCenter>(
    '/recommendations/google-ads',
    () => apiClient.getGoogleAdsCommandCenter(),
    {
      revalidateOnFocus: false,
      refreshInterval: 60000,
    }
  )

  return {
    commandCenter: data || null,
    isLoading,
    isError: !!error,
    error: error ? apiClient.getErrorMessage(error) : null,
    mutate,
  }
}
