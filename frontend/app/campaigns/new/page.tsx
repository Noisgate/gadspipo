'use client'

import Link from 'next/link'
import React, { ChangeEvent, startTransition, useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'

import { Header } from '@/components/dashboard/Header'
import { useAuth } from '@/contexts/auth'
import { apiClient } from '@/lib/api-client'
import {
  CampaignStudioAnalysis,
  CampaignStudioBrief,
  CampaignStudioIdeaAnalysis,
  CampaignStudioRequirement,
  CampaignStudioUploadedMaterial,
} from '@/types'

const assetOptions = [
  { value: 'logo', label: 'Logo da marca' },
  { value: 'product_images', label: 'Imagens do produto/servico' },
  { value: 'lifestyle_images', label: 'Imagens em contexto de uso' },
  { value: 'video', label: 'Video curto' },
  { value: 'landing_page', label: 'Landing page pronta' },
  { value: 'testimonials', label: 'Depoimentos / provas' },
  { value: 'brand_guide', label: 'Guia visual da marca' },
  { value: 'feed', label: 'Feed/catalogo' },
]

const documentOptions = [
  { value: 'price_list', label: 'Tabela de precos' },
  { value: 'compliance_policy', label: 'Politica/compliance' },
  { value: 'privacy_policy', label: 'Politica de privacidade' },
  { value: 'sales_script', label: 'Script comercial' },
  { value: 'offer_doc', label: 'Documento da oferta' },
  { value: 'case_studies', label: 'Cases/resultados' },
]

const initialBrief: CampaignStudioBrief = {
  business_name: '',
  product_or_service: '',
  offer: '',
  objective: 'LEADS',
  intention: '',
  target_audience: '',
  location: 'Sao Paulo',
  budget_amount: 80,
  budget_period: 'daily',
  website_url: '',
  conversion_goal: '',
  differentiators: '',
  current_assets: [],
  available_documents: [],
  notes: '',
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    maximumFractionDigits: 2,
  }).format(value)
}

function formatFileSize(sizeBytes: number) {
  if (sizeBytes >= 1024 * 1024) {
    return `${(sizeBytes / (1024 * 1024)).toFixed(1)} MB`
  }
  return `${Math.max(1, Math.round(sizeBytes / 1024))} KB`
}

function mergeUnique(values: Array<string | null | undefined>) {
  return Array.from(new Set(values.filter(Boolean).map((value) => `${value}`)))
}

function readinessLabel(status: CampaignStudioAnalysis['launch_readiness']['status']) {
  if (status === 'READY_FOR_SETUP') return 'Pronto para setup'
  if (status === 'NEEDS_INPUT') return 'Precisa fechar informacoes'
  return 'Bloqueado para publicacao'
}

function requirementTone(requirement: CampaignStudioRequirement) {
  if (requirement.status === 'ready') return 'border-emerald-200 bg-emerald-50'
  if (requirement.priority === 'HIGH') return 'border-red-200 bg-red-50'
  return 'border-amber-200 bg-amber-50'
}

function materialTone(material: CampaignStudioUploadedMaterial) {
  if (material.kind === 'asset') return 'border-sky-200 bg-sky-50'
  if (material.kind === 'document') return 'border-amber-200 bg-amber-50'
  return 'border-gray-200 bg-gray-50'
}

function materialLabel(material: CampaignStudioUploadedMaterial) {
  if (material.mapped_asset) {
    return assetOptions.find((option) => option.value === material.mapped_asset)?.label ?? material.mapped_asset
  }
  if (material.mapped_document) {
    return documentOptions.find((option) => option.value === material.mapped_document)?.label ?? material.mapped_document
  }
  return 'Material geral'
}

function mergeMaterialState(
  previous: CampaignStudioUploadedMaterial[],
  next: CampaignStudioUploadedMaterial[]
) {
  const map = new Map<string, CampaignStudioUploadedMaterial>()
  ;[...previous, ...next].forEach((material) => {
    map.set(material.id, material)
  })
  return Array.from(map.values())
}

function hydrateBrief(
  current: CampaignStudioBrief,
  suggestion: Partial<CampaignStudioBrief>,
  materials: CampaignStudioUploadedMaterial[]
): CampaignStudioBrief {
  const materialAssets = materials.map((material) => material.mapped_asset).filter(Boolean) as string[]
  const materialDocuments = materials
    .map((material) => material.mapped_document)
    .filter(Boolean) as string[]

  return {
    business_name: current.business_name || suggestion.business_name || '',
    product_or_service: current.product_or_service || suggestion.product_or_service || '',
    offer: current.offer || suggestion.offer || '',
    objective: suggestion.objective || current.objective,
    intention: current.intention || suggestion.intention || '',
    target_audience: current.target_audience || suggestion.target_audience || '',
    location: current.location || suggestion.location || 'Sao Paulo',
    budget_amount: suggestion.budget_amount || current.budget_amount || 80,
    budget_period: suggestion.budget_period || current.budget_period,
    website_url: current.website_url || suggestion.website_url || '',
    conversion_goal: current.conversion_goal || suggestion.conversion_goal || '',
    differentiators: current.differentiators || suggestion.differentiators || '',
    current_assets: mergeUnique([
      ...current.current_assets,
      ...(suggestion.current_assets ?? []),
      ...materialAssets,
    ]),
    available_documents: mergeUnique([
      ...current.available_documents,
      ...(suggestion.available_documents ?? []),
      ...materialDocuments,
    ]),
    notes: mergeUnique([current.notes, suggestion.notes]).join(' '),
  }
}

function StepBadge({
  number,
  label,
  active,
}: {
  number: number
  label: string
  active: boolean
}) {
  return (
    <div className={`rounded-2xl border px-4 py-3 ${active ? 'border-slate-900 bg-slate-900 text-white' : 'border-gray-200 bg-white text-gray-600'}`}>
      <p className="text-xs uppercase tracking-wide">{`Etapa ${number}`}</p>
      <p className="mt-1 text-sm font-semibold">{label}</p>
    </div>
  )
}

function TextInput({
  label,
  value,
  onChange,
  placeholder,
  required,
  type = 'text',
}: {
  label: string
  value?: string | number
  onChange: (value: string) => void
  placeholder?: string
  required?: boolean
  type?: 'text' | 'url' | 'number'
}) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-gray-700">
        {label}
        {required ? ' *' : ''}
      </span>
      <input
        type={type}
        value={value ?? ''}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="mt-2 w-full rounded-xl border border-gray-300 px-4 py-3 text-sm text-gray-900 shadow-sm outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-200"
      />
    </label>
  )
}

function TextArea({
  label,
  value,
  onChange,
  placeholder,
  required,
  rows = 4,
}: {
  label: string
  value?: string
  onChange: (value: string) => void
  placeholder?: string
  required?: boolean
  rows?: number
}) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-gray-700">
        {label}
        {required ? ' *' : ''}
      </span>
      <textarea
        value={value ?? ''}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        rows={rows}
        className="mt-2 w-full rounded-xl border border-gray-300 px-4 py-3 text-sm text-gray-900 shadow-sm outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-200"
      />
    </label>
  )
}

export default function NewCampaignPage() {
  const router = useRouter()
  const { token, isInitialized } = useAuth()
  const [brief, setBrief] = useState<CampaignStudioBrief>(initialBrief)
  const [analysis, setAnalysis] = useState<CampaignStudioAnalysis | null>(null)
  const [ideaAnalysis, setIdeaAnalysis] = useState<CampaignStudioIdeaAnalysis | null>(null)
  const [ideaInput, setIdeaInput] = useState('')
  const [uploadedMaterials, setUploadedMaterials] = useState<CampaignStudioUploadedMaterial[]>([])
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3>(1)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isDiagnosing, setIsDiagnosing] = useState(false)
  const [isUploading, setIsUploading] = useState(false)

  useEffect(() => {
    if (isInitialized && !token) {
      router.push('/login')
    }
  }, [token, isInitialized, router])

  const missingHighPriorityCount = useMemo(() => {
    if (!analysis) return 0
    return [...analysis.asset_requirements, ...analysis.information_requirements].filter(
      (item) => item.priority === 'HIGH' && item.status !== 'ready'
    ).length
  }, [analysis])

  const updateBrief = <K extends keyof CampaignStudioBrief>(key: K, value: CampaignStudioBrief[K]) => {
    setBrief((previous) => ({
      ...previous,
      [key]: value,
    }))
  }

  const toggleArrayValue = (key: 'current_assets' | 'available_documents', value: string) => {
    setBrief((previous) => {
      const current = previous[key]
      const nextValues = current.includes(value)
        ? current.filter((item) => item !== value)
        : [...current, value]

      return {
        ...previous,
        [key]: nextValues,
      }
    })
  }

  const handleUploadMaterials = async (event: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files ?? [])
    if (!files.length) {
      return
    }

    try {
      setIsUploading(true)
      const uploaded = await apiClient.uploadCampaignStudioMaterials(files)
      setUploadedMaterials((previous) => mergeMaterialState(previous, uploaded))
      setIdeaAnalysis((previous) =>
        previous
          ? {
              ...previous,
              uploaded_materials: mergeMaterialState(previous.uploaded_materials, uploaded),
            }
          : previous
      )
      setBrief((previous) => hydrateBrief(previous, {}, uploaded))
      toast.success(`${uploaded.length} material(is) processado(s) pelo estúdio`)
    } catch (error: any) {
      toast.error(apiClient.getErrorMessage(error))
    } finally {
      event.target.value = ''
      setIsUploading(false)
    }
  }

  const handleDiagnoseIdea = async () => {
    if (ideaInput.trim().length < 10) {
      toast.error('Descreva melhor o que voce quer criar para o estúdio conseguir ajudar')
      return
    }

    try {
      setIsDiagnosing(true)
      const response = await apiClient.diagnoseCampaignStudioIdea({
        request: ideaInput,
        objective: brief.objective,
        budget_amount: brief.budget_amount,
        budget_period: brief.budget_period,
        location: brief.location,
        uploaded_materials: uploadedMaterials,
      })
      setIdeaAnalysis(response)
      setBrief((previous) => hydrateBrief(previous, response.suggested_brief, response.uploaded_materials))
      startTransition(() => setCurrentStep(2))
      toast.success('Leitura inicial pronta. O briefing ja foi sugerido para voce revisar.')
    } catch (error: any) {
      toast.error(apiClient.getErrorMessage(error))
    } finally {
      setIsDiagnosing(false)
    }
  }

  const handleAnalyze = async () => {
    try {
      setIsSubmitting(true)
      const response = await apiClient.analyzeCampaignStudioBrief(brief)
      setAnalysis(response)
      startTransition(() => setCurrentStep(3))
      toast.success('Plano inicial da campanha gerado')
    } catch (error: any) {
      toast.error(apiClient.getErrorMessage(error))
    } finally {
      setIsSubmitting(false)
    }
  }

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
    <div className="min-h-screen bg-[#f5f2ea]">
      <Header />

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="rounded-[32px] bg-[radial-gradient(circle_at_top_left,_#fff7d9,_#f2ead9_50%,_#e7dfd0_100%)] p-6 shadow-lg">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
            <div className="max-w-3xl">
              <Link
                href="/campaigns"
                className="inline-flex rounded-full border border-slate-300 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-700 transition hover:bg-white/70"
              >
                Voltar para campanhas
              </Link>
              <h1 className="mt-4 text-3xl font-semibold text-slate-900">Campaign Studio</h1>
              <p className="mt-3 text-sm text-slate-700">
                Agora o estúdio começa do jeito certo: voce descreve a campanha, manda materiais,
                recebe uma leitura inicial e so depois parte para o briefing tecnico e o plano.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              <StepBadge number={1} label="Analisador" active={currentStep === 1} />
              <StepBadge number={2} label="Briefing" active={currentStep === 2} />
              <StepBadge number={3} label="Plano" active={currentStep === 3} />
            </div>
          </div>
        </div>

        <div className="mt-8 grid gap-8 xl:grid-cols-[1.1fr,0.9fr]">
          <section className="space-y-8">
            <section className="rounded-[28px] bg-white p-6 shadow-sm">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">1. Diga o que voce quer criar</h2>
                  <p className="mt-2 text-sm text-gray-600">
                    Conte sua intencao em linguagem natural. O estúdio vai traduzir isso em uma
                    primeira estrutura de Google Ads e te dizer o que ainda precisa chegar.
                  </p>
                </div>
                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-700">
                  entrada guiada
                </span>
              </div>

              <div className="mt-6">
                <TextArea
                  label="O que voce quer criar"
                  value={ideaInput}
                  onChange={setIdeaInput}
                  rows={6}
                  required
                  placeholder="Ex.: Quero captar leads para vender seminovos premium em Sao Paulo, com atendimento por WhatsApp em ate 5 minutos, budget de R$ 120 por dia e foco em pessoas prontas para trocar de carro."
                />
              </div>

              <div className="mt-5 grid gap-5 md:grid-cols-3">
                <label className="block">
                  <span className="text-sm font-medium text-gray-700">Objetivo inicial</span>
                  <select
                    value={brief.objective}
                    onChange={(event) => updateBrief('objective', event.target.value as CampaignStudioBrief['objective'])}
                    className="mt-2 w-full rounded-xl border border-gray-300 px-4 py-3 text-sm text-gray-900 shadow-sm outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-200"
                  >
                    <option value="LEADS">Leads</option>
                    <option value="SALES">Vendas</option>
                    <option value="TRAFFIC">Trafego</option>
                    <option value="AWARENESS">Awareness</option>
                  </select>
                </label>

                <TextInput
                  label="Budget inicial"
                  type="number"
                  value={brief.budget_amount}
                  onChange={(value) => updateBrief('budget_amount', Number(value) || 0)}
                  placeholder="80"
                />

                <label className="block">
                  <span className="text-sm font-medium text-gray-700">Periodo do budget</span>
                  <select
                    value={brief.budget_period}
                    onChange={(event) => updateBrief('budget_period', event.target.value as CampaignStudioBrief['budget_period'])}
                    className="mt-2 w-full rounded-xl border border-gray-300 px-4 py-3 text-sm text-gray-900 shadow-sm outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-200"
                  >
                    <option value="daily">Diario</option>
                    <option value="monthly">Mensal</option>
                  </select>
                </label>
              </div>

              <div className="mt-5">
                <TextInput
                  label="Geografia inicial"
                  value={brief.location}
                  onChange={(value) => updateBrief('location', value)}
                  placeholder="Ex.: Sao Paulo e Grande SP"
                />
              </div>

              <div className="mt-6 rounded-[24px] border border-dashed border-slate-300 bg-slate-50 p-5">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div className="max-w-2xl">
                    <h3 className="text-lg font-semibold text-slate-900">2. Mande os materiais que voce ja tem</h3>
                    <p className="mt-2 text-sm text-slate-600">
                      Pode mandar logo, imagens, videos, tabela comercial, politica de privacidade,
                      cases, roteiro comercial e outros arquivos. O estúdio classifica tudo automaticamente.
                    </p>
                  </div>
                  <label className="inline-flex cursor-pointer items-center justify-center rounded-xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800">
                    {isUploading ? 'Enviando...' : 'Enviar materiais'}
                    <input
                      type="file"
                      multiple
                      onChange={handleUploadMaterials}
                      className="hidden"
                      accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.xml,.jpg,.jpeg,.png,.webp,.mp4,.mov,.avi"
                    />
                  </label>
                </div>

                <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  {['Logo', 'Imagens do produto', 'Videos curtos', 'Tabela comercial', 'Cases e provas', 'Politicas e termos'].map((item) => (
                    <div key={item} className="rounded-2xl bg-white px-4 py-3 text-sm text-slate-700 shadow-sm">
                      {item}
                    </div>
                  ))}
                </div>

                {uploadedMaterials.length > 0 ? (
                  <div className="mt-6 space-y-3">
                    {uploadedMaterials.map((material) => (
                      <div key={material.id} className={`rounded-2xl border p-4 ${materialTone(material)}`}>
                        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                          <div>
                            <p className="font-medium text-gray-900">{material.original_name}</p>
                            <p className="mt-1 text-sm text-gray-600">
                              {materialLabel(material)} • {formatFileSize(material.size_bytes)}
                            </p>
                          </div>
                          <span className="rounded-full bg-white/80 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-gray-700">
                            {material.kind}
                          </span>
                        </div>
                        {material.notes ? <p className="mt-3 text-sm text-gray-700">{material.notes}</p> : null}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="mt-6 rounded-2xl bg-white px-4 py-4 text-sm text-gray-600 shadow-sm">
                    Nenhum material enviado ainda. Voce pode analisar a ideia agora e subir os arquivos logo depois.
                  </div>
                )}
              </div>

              <div className="mt-6 flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={handleDiagnoseIdea}
                  disabled={isDiagnosing}
                  className="rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isDiagnosing ? 'Analisando ideia...' : 'Analisar ideia e montar briefing'}
                </button>
                <p className="text-sm text-gray-500">
                  Esse passo interpreta sua intencao, organiza os materiais e preenche um briefing inicial.
                </p>
              </div>
            </section>

            <section className="rounded-[28px] bg-white p-6 shadow-sm">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">2. Refinar briefing</h2>
                  <p className="mt-2 text-sm text-gray-600">
                    Aqui voce ajusta o que o analisador entendeu e fecha os campos essenciais antes do plano.
                  </p>
                </div>
                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-700">
                  briefing editavel
                </span>
              </div>

              <div className="mt-6 grid gap-5 md:grid-cols-2">
                <TextInput
                  label="Nome da marca"
                  value={brief.business_name}
                  onChange={(value) => updateBrief('business_name', value)}
                  placeholder="Ex.: Aramatti Seminovos"
                />
                <TextInput
                  label="Produto ou servico"
                  value={brief.product_or_service}
                  onChange={(value) => updateBrief('product_or_service', value)}
                  placeholder="Ex.: seminovos premium"
                  required
                />
                <TextInput
                  label="Oferta"
                  value={brief.offer}
                  onChange={(value) => updateBrief('offer', value)}
                  placeholder="Ex.: avaliacao + atendimento rapido"
                  required
                />
                <label className="block">
                  <span className="text-sm font-medium text-gray-700">Objetivo principal *</span>
                  <select
                    value={brief.objective}
                    onChange={(event) => updateBrief('objective', event.target.value as CampaignStudioBrief['objective'])}
                    className="mt-2 w-full rounded-xl border border-gray-300 px-4 py-3 text-sm text-gray-900 shadow-sm outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-200"
                  >
                    <option value="LEADS">Leads</option>
                    <option value="SALES">Vendas</option>
                    <option value="TRAFFIC">Trafego</option>
                    <option value="AWARENESS">Awareness</option>
                  </select>
                </label>
              </div>

              <div className="mt-5">
                <TextArea
                  label="Intencao da campanha"
                  value={brief.intention}
                  onChange={(value) => updateBrief('intention', value)}
                  placeholder="Ex.: Quero captar leads para vender seminovos em Sao Paulo com time comercial respondendo em ate 5 minutos."
                  required
                />
              </div>

              <div className="mt-5 grid gap-5 md:grid-cols-2">
                <TextInput
                  label="Publico-alvo"
                  value={brief.target_audience}
                  onChange={(value) => updateBrief('target_audience', value)}
                  placeholder="Ex.: pessoas buscando trocar de carro"
                  required
                />
                <TextInput
                  label="Localizacao"
                  value={brief.location}
                  onChange={(value) => updateBrief('location', value)}
                  placeholder="Ex.: Sao Paulo e Grande SP"
                  required
                />
                <TextInput
                  label="Budget"
                  type="number"
                  value={brief.budget_amount}
                  onChange={(value) => updateBrief('budget_amount', Number(value) || 0)}
                  placeholder="80"
                  required
                />
                <label className="block">
                  <span className="text-sm font-medium text-gray-700">Periodo do budget *</span>
                  <select
                    value={brief.budget_period}
                    onChange={(event) => updateBrief('budget_period', event.target.value as CampaignStudioBrief['budget_period'])}
                    className="mt-2 w-full rounded-xl border border-gray-300 px-4 py-3 text-sm text-gray-900 shadow-sm outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-200"
                  >
                    <option value="daily">Diario</option>
                    <option value="monthly">Mensal</option>
                  </select>
                </label>
                <TextInput
                  label="URL final"
                  type="url"
                  value={brief.website_url}
                  onChange={(value) => updateBrief('website_url', value)}
                  placeholder="https://seusite.com/oferta"
                />
                <TextInput
                  label="Meta de conversao"
                  value={brief.conversion_goal}
                  onChange={(value) => updateBrief('conversion_goal', value)}
                  placeholder="Ex.: lead qualificado no formulario"
                />
              </div>

              <div className="mt-5">
                <TextArea
                  label="Diferenciais"
                  value={brief.differentiators}
                  onChange={(value) => updateBrief('differentiators', value)}
                  placeholder="Ex.: garantia, procedencia, entrega rapida, financiamento agil"
                />
              </div>

              <div className="mt-6 grid gap-6 lg:grid-cols-2">
                <div className="rounded-2xl border border-gray-200 p-5">
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-700">Assets que voce ja tem</h3>
                  <div className="mt-4 space-y-3">
                    {assetOptions.map((option) => (
                      <label key={option.value} className="flex items-center gap-3 text-sm text-gray-700">
                        <input
                          type="checkbox"
                          checked={brief.current_assets.includes(option.value)}
                          onChange={() => toggleArrayValue('current_assets', option.value)}
                          className="h-4 w-4 rounded border-gray-300 text-slate-900 focus:ring-slate-300"
                        />
                        {option.label}
                      </label>
                    ))}
                  </div>
                </div>

                <div className="rounded-2xl border border-gray-200 p-5">
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-700">Documentos e materiais</h3>
                  <div className="mt-4 space-y-3">
                    {documentOptions.map((option) => (
                      <label key={option.value} className="flex items-center gap-3 text-sm text-gray-700">
                        <input
                          type="checkbox"
                          checked={brief.available_documents.includes(option.value)}
                          onChange={() => toggleArrayValue('available_documents', option.value)}
                          className="h-4 w-4 rounded border-gray-300 text-slate-900 focus:ring-slate-300"
                        />
                        {option.label}
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              <div className="mt-5">
                <TextArea
                  label="Observacoes adicionais"
                  value={brief.notes}
                  onChange={(value) => updateBrief('notes', value)}
                  placeholder="Ex.: time comercial atende por WhatsApp, queremos evitar curiosos e priorizar leads quentes."
                />
              </div>

              <div className="mt-6 flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={handleAnalyze}
                  disabled={isSubmitting}
                  className="rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isSubmitting ? 'Gerando plano...' : 'Gerar plano completo'}
                </button>
                <p className="text-sm text-gray-500">
                  Aqui a campanha vira estrutura, checklist, copy inicial e bloqueios reais de setup.
                </p>
              </div>
            </section>
          </section>

          <aside className="space-y-6">
            <section className="rounded-[28px] bg-slate-900 p-6 text-white shadow-sm">
              <p className="text-xs uppercase tracking-[0.2em] text-white/60">Estudio</p>
              <h2 className="mt-3 text-2xl font-semibold">O que mudou neste fluxo</h2>
              <div className="mt-5 space-y-3 text-sm text-white/80">
                <p>Voce escreve a intencao em linguagem natural</p>
                <p>O sistema pede e classifica materiais de verdade</p>
                <p>O briefing ja chega pre-preenchido para revisao</p>
                <p>So depois vem o plano tecnico da campanha</p>
              </div>
            </section>

            {ideaAnalysis ? (
              <section className="rounded-[28px] bg-white p-6 shadow-sm">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-wide text-gray-500">Analisador</p>
                    <h3 className="mt-2 text-xl font-semibold text-gray-900">Leitura inicial pronta</h3>
                  </div>
                  <div className="rounded-2xl bg-gray-50 px-4 py-3 text-right">
                    <p className="text-xs uppercase tracking-wide text-gray-500">Tipo sugerido</p>
                    <p className="mt-1 text-sm font-semibold text-gray-900">
                      {ideaAnalysis.suggested_campaign_type}
                    </p>
                  </div>
                </div>

                <p className="mt-4 text-sm text-gray-600">{ideaAnalysis.summary}</p>

                <div className="mt-5 flex flex-wrap gap-2">
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                    {ideaAnalysis.suggested_campaign_type}
                  </span>
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                    {ideaAnalysis.suggested_bidding_strategy}
                  </span>
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                    {ideaAnalysis.ai_metadata.used_ai ? 'IA ativa' : 'Motor estruturado'}
                  </span>
                </div>
              </section>
            ) : (
              <section className="rounded-[28px] bg-white p-6 shadow-sm">
                <h3 className="text-lg font-semibold text-gray-900">Antes do briefing</h3>
                <p className="mt-3 text-sm text-gray-600">
                  O analisador vai resumir o que voce quer criar, sugerir tipo de campanha,
                  mostrar perguntas pendentes e dizer quais materiais faltam.
                </p>
              </section>
            )}

            {ideaAnalysis ? (
              <>
                <section className="rounded-[28px] bg-white p-6 shadow-sm">
                  <h3 className="text-lg font-semibold text-gray-900">Perguntas que ainda faltam</h3>
                  <div className="mt-4 space-y-3">
                    {ideaAnalysis.questions_to_clarify.map((item) => (
                      <div key={item} className="rounded-xl border border-gray-200 px-4 py-3 text-sm text-gray-700">
                        {item}
                      </div>
                    ))}
                  </div>
                </section>

                <section className="rounded-[28px] bg-white p-6 shadow-sm">
                  <h3 className="text-lg font-semibold text-gray-900">Materiais que o estúdio quer receber</h3>
                  <div className="mt-4 space-y-3">
                    {ideaAnalysis.material_requirements.map((item) => (
                      <div key={item.item} className={`rounded-2xl border p-4 ${requirementTone(item)}`}>
                        <div className="flex items-center justify-between gap-4">
                          <p className="font-medium text-gray-900">{item.item}</p>
                          <span className="rounded-full bg-white/80 px-2 py-1 text-xs font-semibold text-gray-700">
                            {item.priority}
                          </span>
                        </div>
                        <p className="mt-2 text-sm text-gray-700">{item.reason}</p>
                        {item.example ? <p className="mt-2 text-sm text-gray-600">Exemplo: {item.example}</p> : null}
                      </div>
                    ))}
                  </div>
                </section>

                <section className="rounded-[28px] bg-white p-6 shadow-sm">
                  <h3 className="text-lg font-semibold text-gray-900">Proximos passos sugeridos</h3>
                  <div className="mt-4 space-y-3">
                    {ideaAnalysis.next_steps.map((item) => (
                      <div key={item} className="rounded-xl bg-gray-50 px-4 py-3 text-sm text-gray-700">
                        {item}
                      </div>
                    ))}
                  </div>
                </section>
              </>
            ) : null}

            {analysis ? (
              <section className="rounded-[28px] bg-white p-6 shadow-sm">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-wide text-gray-500">Prontidao</p>
                    <h3 className="mt-2 text-xl font-semibold text-gray-900">
                      {readinessLabel(analysis.launch_readiness.status)}
                    </h3>
                  </div>
                  <div className="rounded-2xl bg-gray-50 px-4 py-3 text-right">
                    <p className="text-xs uppercase tracking-wide text-gray-500">Score</p>
                    <p className="mt-1 text-2xl font-semibold text-gray-900">
                      {analysis.launch_readiness.score}/100
                    </p>
                  </div>
                </div>

                <p className="mt-4 text-sm text-gray-600">{analysis.briefing_digest.summary}</p>

                <div className="mt-5 rounded-2xl border border-amber-200 bg-amber-50 p-4">
                  <p className="text-sm font-medium text-amber-900">
                    {missingHighPriorityCount} pendencia(s) de alta prioridade
                  </p>
                  <p className="mt-2 text-sm text-amber-800">
                    Resolva primeiro os itens marcados como `HIGH` para a campanha chegar pronta no setup.
                  </p>
                </div>
              </section>
            ) : null}
          </aside>
        </div>

        {analysis ? (
          <div className="mt-8 space-y-8">
            <section className="grid gap-6 xl:grid-cols-[1.15fr,0.85fr]">
              <div className="rounded-[28px] bg-white p-6 shadow-sm">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h2 className="text-2xl font-semibold text-gray-900">3. Plano inicial</h2>
                    <p className="mt-2 text-sm text-gray-600">
                      Estrategia recomendada para sair da ideia e entrar no Google Ads com menos retrabalho.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setCurrentStep(2)}
                    className="rounded-full border border-gray-300 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-gray-700 transition hover:bg-gray-50"
                  >
                    Editar briefing
                  </button>
                </div>

                <div className="mt-6 grid gap-4 md:grid-cols-3">
                  <div className="rounded-2xl border border-gray-200 p-4">
                    <p className="text-xs uppercase tracking-wide text-gray-500">Tipo recomendado</p>
                    <p className="mt-2 text-lg font-semibold text-gray-900">
                      {analysis.strategic_recommendation.recommended_campaign_type}
                    </p>
                  </div>
                  <div className="rounded-2xl border border-gray-200 p-4">
                    <p className="text-xs uppercase tracking-wide text-gray-500">Lance sugerido</p>
                    <p className="mt-2 text-lg font-semibold text-gray-900">
                      {analysis.strategic_recommendation.recommended_bidding_strategy}
                    </p>
                  </div>
                  <div className="rounded-2xl border border-gray-200 p-4">
                    <p className="text-xs uppercase tracking-wide text-gray-500">Nome sugerido</p>
                    <p className="mt-2 text-lg font-semibold text-gray-900">
                      {analysis.campaign_blueprint.suggested_campaign_name}
                    </p>
                  </div>
                </div>

                <div className="mt-6 rounded-2xl bg-gray-50 p-5">
                  <p className="text-sm font-medium text-gray-900">Leitura do estúdio</p>
                  <p className="mt-2 text-sm text-gray-700">{analysis.briefing_digest.summary}</p>
                  <p className="mt-3 text-sm text-gray-600">
                    {analysis.strategic_recommendation.budget_explanation}
                  </p>
                </div>

                <div className="mt-6 grid gap-6 lg:grid-cols-2">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">Por que essa estrutura</h3>
                    <div className="mt-3 space-y-3">
                      {analysis.strategic_recommendation.rationale.map((item) => (
                        <div key={item} className="rounded-xl border border-gray-200 px-4 py-3 text-sm text-gray-700">
                          {item}
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">Sequencia de lancamento</h3>
                    <div className="mt-3 space-y-3">
                      {analysis.strategic_recommendation.launch_sequence.map((item) => (
                        <div key={item} className="rounded-xl border border-gray-200 px-4 py-3 text-sm text-gray-700">
                          {item}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              <div className="rounded-[28px] bg-white p-6 shadow-sm">
                <h2 className="text-xl font-semibold text-gray-900">Bloqueios e proximos passos</h2>
                <p className="mt-2 text-sm text-gray-600">
                  O que falta fechar para transformar esse plano em campanha publicavel.
                </p>

                <div className="mt-5 space-y-3">
                  {analysis.launch_readiness.blockers.length > 0 ? (
                    analysis.launch_readiness.blockers.map((blocker) => (
                      <div key={blocker} className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
                        {blocker}
                      </div>
                    ))
                  ) : (
                    <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
                      Nenhum bloqueio critico detectado. Ja da para seguir para setup interno.
                    </div>
                  )}
                </div>

                <div className="mt-6 space-y-3">
                  {analysis.launch_readiness.next_steps.map((step) => (
                    <div key={step} className="rounded-xl bg-gray-50 px-4 py-3 text-sm text-gray-700">
                      {step}
                    </div>
                  ))}
                </div>

                <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-xs uppercase tracking-wide text-slate-500">Gerador</p>
                  <p className="mt-2 text-sm font-medium text-slate-900">
                    {analysis.ai_metadata.used_ai ? 'IA ativa no enriquecimento' : 'Motor estrategico estruturado'}
                  </p>
                  <p className="mt-1 text-sm text-slate-600">{analysis.ai_metadata.model}</p>
                </div>
              </div>
            </section>

            <section className="rounded-[28px] bg-white p-6 shadow-sm">
              <h2 className="text-xl font-semibold text-gray-900">Blueprint da campanha</h2>
              <p className="mt-2 text-sm text-gray-600">
                Estrutura base para entrar no Google Ads com separacao de intencao e leitura de performance.
              </p>

              <div className="mt-6 grid gap-4 xl:grid-cols-3">
                {analysis.campaign_blueprint.ad_groups.map((adGroup) => (
                  <div key={adGroup.name} className="rounded-2xl border border-gray-200 p-5">
                    <h3 className="text-lg font-semibold text-gray-900">{adGroup.name}</h3>
                    <p className="mt-2 text-sm text-gray-600">{adGroup.intent}</p>
                    <p className="mt-4 text-xs uppercase tracking-wide text-gray-500">Temas de keyword</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {adGroup.keyword_themes.map((theme) => (
                        <span key={theme} className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                          {theme}
                        </span>
                      ))}
                    </div>
                    <p className="mt-4 text-xs uppercase tracking-wide text-gray-500">Foco da landing</p>
                    <p className="mt-2 text-sm text-gray-700">{adGroup.landing_page_focus}</p>
                  </div>
                ))}
              </div>

              <div className="mt-6 grid gap-6 lg:grid-cols-2">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Negativas iniciais</h3>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {analysis.campaign_blueprint.negative_keyword_themes.map((item) => (
                      <span key={item} className="rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-800">
                        {item}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Extensoes sugeridas</h3>
                  <div className="mt-3 space-y-2">
                    {analysis.campaign_blueprint.ad_extensions.map((item) => (
                      <div key={item} className="rounded-xl bg-gray-50 px-4 py-3 text-sm text-gray-700">
                        {item}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </section>

            <section className="grid gap-6 xl:grid-cols-2">
              <div className="rounded-[28px] bg-white p-6 shadow-sm">
                <h2 className="text-xl font-semibold text-gray-900">Assets e materiais</h2>
                <p className="mt-2 text-sm text-gray-600">
                  Aqui fica claro o que ja existe, o que ainda falta e o que seria bom providenciar.
                </p>
                <div className="mt-5 space-y-3">
                  {analysis.asset_requirements.map((item) => (
                    <div key={item.item} className={`rounded-2xl border p-4 ${requirementTone(item)}`}>
                      <div className="flex items-center justify-between gap-4">
                        <p className="font-medium text-gray-900">{item.item}</p>
                        <span className="rounded-full bg-white/80 px-2 py-1 text-xs font-semibold text-gray-700">
                          {item.priority}
                        </span>
                      </div>
                      <p className="mt-2 text-sm text-gray-700">{item.reason}</p>
                      {item.example ? <p className="mt-2 text-sm text-gray-600">Exemplo: {item.example}</p> : null}
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-[28px] bg-white p-6 shadow-sm">
                <h2 className="text-xl font-semibold text-gray-900">Informacoes que ainda precisamos</h2>
                <p className="mt-2 text-sm text-gray-600">
                  Esses itens fecham o briefing e evitam setup torto, copy fraca ou publicacao prematura.
                </p>
                <div className="mt-5 space-y-3">
                  {analysis.information_requirements.map((item) => (
                    <div key={item.item} className={`rounded-2xl border p-4 ${requirementTone(item)}`}>
                      <div className="flex items-center justify-between gap-4">
                        <p className="font-medium text-gray-900">{item.item}</p>
                        <span className="rounded-full bg-white/80 px-2 py-1 text-xs font-semibold text-gray-700">
                          {item.priority}
                        </span>
                      </div>
                      <p className="mt-2 text-sm text-gray-700">{item.reason}</p>
                      {item.example ? <p className="mt-2 text-sm text-gray-600">Exemplo: {item.example}</p> : null}
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <section className="grid gap-6 xl:grid-cols-[1fr,1fr,0.9fr]">
              <div className="rounded-[28px] bg-white p-6 shadow-sm">
                <h2 className="text-xl font-semibold text-gray-900">Mensagens iniciais</h2>
                <p className="mt-2 text-sm text-gray-600">
                  Angulos e copys para acelerar o setup da primeira versao da campanha.
                </p>

                <div className="mt-5">
                  <p className="text-sm font-semibold uppercase tracking-wide text-gray-500">Angulos</p>
                  <div className="mt-3 space-y-2">
                    {analysis.messaging.angles.map((item) => (
                      <div key={item} className="rounded-xl bg-gray-50 px-4 py-3 text-sm text-gray-700">
                        {item}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="mt-5">
                  <p className="text-sm font-semibold uppercase tracking-wide text-gray-500">Headlines</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {analysis.messaging.headline_ideas.map((item) => (
                      <span key={item} className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                        {item}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="mt-5">
                  <p className="text-sm font-semibold uppercase tracking-wide text-gray-500">Descriptions</p>
                  <div className="mt-3 space-y-2">
                    {analysis.messaging.description_ideas.map((item) => (
                      <div key={item} className="rounded-xl bg-gray-50 px-4 py-3 text-sm text-gray-700">
                        {item}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="rounded-[28px] bg-white p-6 shadow-sm">
                <h2 className="text-xl font-semibold text-gray-900">Tracking e compliance</h2>
                <div className="mt-5">
                  <p className="text-sm font-semibold uppercase tracking-wide text-gray-500">Tracking</p>
                  <div className="mt-3 space-y-2">
                    {analysis.tracking_requirements.map((item) => (
                      <div key={item} className="rounded-xl bg-gray-50 px-4 py-3 text-sm text-gray-700">
                        {item}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="mt-5">
                  <p className="text-sm font-semibold uppercase tracking-wide text-gray-500">Compliance</p>
                  <div className="mt-3 space-y-2">
                    {analysis.compliance_checks.map((item) => (
                      <div key={item} className="rounded-xl bg-gray-50 px-4 py-3 text-sm text-gray-700">
                        {item}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="rounded-[28px] bg-white p-6 shadow-sm">
                <h2 className="text-xl font-semibold text-gray-900">Checklist final</h2>
                <div className="mt-5 space-y-3">
                  {analysis.launch_checklist.map((item) => (
                    <div
                      key={item.label}
                      className={`rounded-2xl border px-4 py-3 text-sm ${
                        item.status === 'ready'
                          ? 'border-emerald-200 bg-emerald-50 text-emerald-900'
                          : item.status === 'warning'
                          ? 'border-amber-200 bg-amber-50 text-amber-900'
                          : 'border-red-200 bg-red-50 text-red-900'
                      }`}
                    >
                      <p className="font-medium">{item.label}</p>
                      <p className="mt-1">{item.detail}</p>
                    </div>
                  ))}
                </div>

                <div className="mt-6 rounded-2xl border border-dashed border-gray-300 p-4">
                  <p className="text-sm font-medium text-gray-900">Proxima fase</p>
                  <p className="mt-2 text-sm text-gray-600">
                    O passo seguinte e salvar drafts com os materiais enviados e ligar a publicacao real no Google Ads.
                  </p>
                </div>
              </div>
            </section>
          </div>
        ) : null}
      </main>
    </div>
  )
}
