import { io } from "next/cache"
import Link from "next/link"
import { Suspense } from "react"
import { FileText, Plus } from "lucide-react"

import { buttonVariants } from "@/components/ui/button"
import {
  Card,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { listBoards } from "@/lib/boards"
import { formatDate } from "@/lib/format"

export default function Home() {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-2">
        <h1 className="text-2xl font-bold tracking-tight">게시판</h1>
        <Link href="/boards/new" className={buttonVariants()}>
          <Plus />
          게시판 만들기
        </Link>
      </div>
      <Suspense fallback={<p className="text-muted-foreground">불러오는 중…</p>}>
        <BoardList />
      </Suspense>
    </div>
  )
}

async function BoardList() {
  await io()
  const boards = await listBoards()

  if (boards.length === 0) {
    return (
      <p className="py-16 text-center text-muted-foreground">
        아직 게시판이 없습니다. &lsquo;게시판 만들기&rsquo;로 첫 게시판을 만들어 보세요.
      </p>
    )
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {boards.map((board) => (
        <Link key={board.id} href={`/boards/${board.id}`} className="group">
          <Card className="h-full transition-colors group-hover:border-primary/60 group-hover:bg-accent/40">
            <CardHeader>
              <CardTitle className="text-lg">{board.name}</CardTitle>
              <CardDescription>
                {board.description || "설명이 없는 게시판입니다."}
              </CardDescription>
            </CardHeader>
            <CardFooter className="mt-auto gap-3 text-sm text-muted-foreground">
              <span className="flex items-center gap-1">
                <FileText className="size-4" />글 {board.postCount}개
              </span>
              {board.lastPostAt && <span>최근 글 {formatDate(board.lastPostAt)}</span>}
            </CardFooter>
          </Card>
        </Link>
      ))}
    </div>
  )
}
