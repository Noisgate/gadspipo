'use client'

import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuth } from '@/contexts/auth'

export function Header() {
  const { user, logout } = useAuth()
  const pathname = usePathname()
  const navItems = [
    { href: '/dashboard', label: 'Visao geral' },
    { href: '/campaigns', label: 'Campanhas' },
    { href: '/recommendations', label: 'Central de decisao' },
  ]

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-4 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
        <div className="flex items-center gap-6">
          <Link href="/dashboard" className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-900 text-sm font-semibold text-white shadow-sm">
              MM
            </div>
            <div>
              <p className="text-base font-semibold text-slate-900">Marketing Manager</p>
              <p className="text-xs uppercase tracking-[0.24em] text-slate-500">
                Google Ads guiado pelo xquads
              </p>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50/80 p-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`)

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`rounded-full px-4 py-2 text-sm font-medium transition ${
                    isActive
                      ? 'bg-slate-900 text-white shadow-sm'
                      : 'text-slate-600 hover:bg-white hover:text-slate-900'
                  }`}
                >
                  {item.label}
                </Link>
              )
            })}
          </nav>
        </div>

        <div className="flex items-center gap-4">
          {user ? (
            <>
              <div className="hidden rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2 text-right sm:block">
                <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Conta conectada</p>
                <p className="text-sm font-medium text-slate-700">{user.email}</p>
              </div>
              <button
                onClick={logout}
                className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-2 text-sm font-medium text-rose-700 transition hover:bg-rose-100"
              >
                Logout
              </button>
            </>
          ) : (
            <Link
              href="/login"
              className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800"
            >
              Login
            </Link>
          )}
        </div>
      </div>
    </header>
  )
}
