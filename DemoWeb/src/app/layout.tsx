import type { Metadata } from "next"
import Link from "next/link"
import { Geist, Geist_Mono } from "next/font/google"
import { MessagesSquare, PenLine } from "lucide-react"

import { buttonVariants } from "@/components/ui/button"
import "./globals.css"

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
})

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
})

export const metadata: Metadata = {
  title: { default: "DemoWeb 게시판", template: "%s | DemoWeb 게시판" },
  description: "Next.js + shadcn/ui로 만든 간단한 게시판",
}

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="ko"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-muted/30">
        <header className="border-b bg-background">
          <div className="mx-auto flex h-14 w-full max-w-4xl items-center justify-between px-4">
            <Link href="/" className="flex items-center gap-2 font-semibold">
              <MessagesSquare className="size-5" />
              DemoWeb 게시판
            </Link>
            <Link href="/posts/new" className={buttonVariants({ size: "sm" })}>
              <PenLine />
              글쓰기
            </Link>
          </div>
        </header>
        <main className="mx-auto w-full max-w-4xl flex-1 px-4 py-6 sm:py-8">
          {children}
        </main>
      </body>
    </html>
  )
}
