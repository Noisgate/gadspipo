'use client'

import React, { useEffect } from 'react'
import { Toaster } from 'sonner'
import { useAuth } from '@/contexts/auth'

export function Providers({ children }: { children: React.ReactNode }) {
  const initAuth = useAuth((state) => state.initAuth)

  useEffect(() => {
    initAuth()
  }, [initAuth])

  return (
    <>
      {children}
      <Toaster position="top-right" richColors />
    </>
  )
}
