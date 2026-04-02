'use client'

import React, { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Header } from '@/components/dashboard/Header'
import { CampaignTable } from '@/components/dashboard/CampaignTable'
import { useAuth } from '@/contexts/auth'
import { useCampaigns } from '@/hooks/useCampaigns'

export default function CampaignsPage() {
  const router = useRouter()
  const { token, isInitialized } = useAuth()
  const { campaigns, isLoading, isError, error } = useCampaigns()
  const activeCampaigns = campaigns.filter((campaign) => campaign.status === 'ENABLED')
  const campaignsWithoutDelivery = campaigns.filter((campaign) => {
    const metrics = campaign.latest_metrics
    return campaign.status === 'ENABLED' && (!metrics || (metrics.impressions === 0 && metrics.clicks === 0))
  })
  const campaignsWithConversions = campaigns.filter(
    (campaign) => (campaign.latest_metrics?.conversions ?? 0) > 0
  )

  useEffect(() => {
    if (isInitialized && !token) {
      router.push('/login')
    }
  }, [token, isInitialized, router])

  if (!isInitialized) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">Carregando...</p>
      </div>
    )
  }

  if (!token) {
    return null
  }

  return (
    <div className="min-h-screen bg-stone-50">
      <Header />

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <section className="rounded-[32px] bg-gradient-to-br from-slate-900 via-slate-800 to-amber-700 p-8 text-white shadow-lg">
          <div className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
            <div className="max-w-3xl">
              <p className="text-xs uppercase tracking-[0.3em] text-white/60">Fila de trabalho</p>
              <h1 className="mt-4 text-3xl font-semibold sm:text-4xl">Campanhas com proximo passo claro</h1>
              <p className="mt-4 text-sm leading-6 text-white/80 sm:text-base">
                Aqui voce nao precisa interpretar Google Ads sozinho. Cada campanha aparece com o que
                parece estar acontecendo e qual analise guiada vale abrir agora.
              </p>
            </div>

            <button
              type="button"
              onClick={() => router.push('/campaigns/new')}
              className="inline-flex items-center justify-center rounded-2xl bg-white px-5 py-3 text-sm font-semibold text-slate-900 transition hover:bg-slate-100"
            >
              Nova campanha guiada
            </button>
          </div>

          <div className="mt-8 grid gap-3 md:grid-cols-3">
            <div className="rounded-2xl bg-white/10 px-5 py-4 backdrop-blur">
              <p className="text-xs uppercase tracking-[0.24em] text-white/60">Ativas</p>
              <p className="mt-2 text-3xl font-semibold">{activeCampaigns.length}</p>
              <p className="mt-2 text-sm text-white/75">Campanhas que deveriam estar rodando agora.</p>
            </div>
            <div className="rounded-2xl bg-white/10 px-5 py-4 backdrop-blur">
              <p className="text-xs uppercase tracking-[0.24em] text-white/60">Sem entrega</p>
              <p className="mt-2 text-3xl font-semibold">{campaignsWithoutDelivery.length}</p>
              <p className="mt-2 text-sm text-white/75">Prioridade para investigar antes de otimizar.</p>
            </div>
            <div className="rounded-2xl bg-white/10 px-5 py-4 backdrop-blur">
              <p className="text-xs uppercase tracking-[0.24em] text-white/60">Com resultado</p>
              <p className="mt-2 text-3xl font-semibold">{campaignsWithConversions.length}</p>
              <p className="mt-2 text-sm text-white/75">Boas candidatas para ajustes e escala futura.</p>
            </div>
          </div>
        </section>

        <section className="mt-8 grid gap-4 lg:grid-cols-3">
          <div className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm">
            <p className="text-xs uppercase tracking-[0.24em] text-slate-400">1. Escolha</p>
            <h2 className="mt-3 text-lg font-semibold text-slate-900">Abra a campanha certa</h2>
            <p className="mt-2 text-sm text-slate-600">
              As campanhas abaixo ja aparecem ordenadas para voce comecar pelo que esta mais travado.
            </p>
          </div>
          <div className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm">
            <p className="text-xs uppercase tracking-[0.24em] text-slate-400">2. Entenda</p>
            <h2 className="mt-3 text-lg font-semibold text-slate-900">Leia em portugues claro</h2>
            <p className="mt-2 text-sm text-slate-600">
              O app explica por que a campanha nao roda, ou por que roda mas nao performa.
            </p>
          </div>
          <div className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm">
            <p className="text-xs uppercase tracking-[0.24em] text-slate-400">3. Aprove</p>
            <h2 className="mt-3 text-lg font-semibold text-slate-900">Deixe o app agir por API</h2>
            <p className="mt-2 text-sm text-slate-600">
              Depois da conversa e do refinamento, voce aprova e o sistema executa o que for seguro.
            </p>
          </div>
        </section>

        {isError ? (
          <div className="mt-8 rounded-[28px] border border-rose-200 bg-white p-6 shadow-sm">
            <p className="font-medium text-rose-600">Nao foi possivel carregar as campanhas.</p>
            <p className="mt-2 text-sm text-slate-600">{error}</p>
          </div>
        ) : (
          <div className="mt-8">
            <CampaignTable
              campaigns={campaigns}
              isLoading={isLoading}
              onCampaignClick={(campaign) => router.push(`/campaigns/${campaign.id}`)}
            />
          </div>
        )}
      </main>
    </div>
  )
}
