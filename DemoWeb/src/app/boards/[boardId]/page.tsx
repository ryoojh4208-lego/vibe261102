import Link from "next/link"
import { notFound } from "next/navigation"
import { Suspense } from "react"
import {
  ChevronLeft,
  ChevronRight,
  Eye,
  Heart,
  MessageSquare,
  PenLine,
  Search,
} from "lucide-react"

import { deleteBoard } from "@/app/actions"
import { ConfirmDeleteButton } from "@/components/confirm-delete-button"
import { Button, buttonVariants } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { getBoard } from "@/lib/boards"
import { formatDate } from "@/lib/format"
import { listPosts } from "@/lib/posts"
import { cn } from "@/lib/utils"

const PAGE_SIZE = 10

export default function BoardPage({ params, searchParams }: PageProps<"/boards/[boardId]">) {
  return (
    <Suspense fallback={<p className="text-muted-foreground">불러오는 중…</p>}>
      <BoardContent params={params} searchParams={searchParams} />
    </Suspense>
  )
}

async function BoardContent({ params, searchParams }: PageProps<"/boards/[boardId]">) {
  const { boardId } = await params
  const board = await getBoard(Number(boardId))
  if (!board) notFound()

  const sp = await searchParams
  const query = typeof sp.q === "string" ? sp.q : ""
  const page = Number(sp.page) || 1
  const { posts, total, totalPages, page: current } = await listPosts({
    boardId: board.id,
    query,
    page,
    pageSize: PAGE_SIZE,
  })

  const pageHref = (p: number) => {
    const qs = new URLSearchParams()
    if (query) qs.set("q", query)
    if (p > 1) qs.set("page", String(p))
    const s = qs.toString()
    return `/boards/${board.id}${s ? `?${s}` : ""}`
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <Link href="/" className="text-sm text-muted-foreground hover:underline">
            게시판 목록
          </Link>
          <h1 className="text-2xl font-bold tracking-tight break-words">{board.name}</h1>
          {board.description && (
            <p className="text-muted-foreground">{board.description}</p>
          )}
        </div>
        <div className="flex gap-2">
          <ConfirmDeleteButton
            action={deleteBoard.bind(null, board.id)}
            title="게시판을 삭제할까요?"
            description={`'${board.name}' 게시판과 안에 있는 글 ${board.postCount}개, 댓글이 모두 영구히 삭제됩니다.`}
            label="게시판 삭제"
          />
          <Link href={`/boards/${board.id}/new`} className={buttonVariants()}>
            <PenLine />
            글쓰기
          </Link>
        </div>
      </div>

      <form action={`/boards/${board.id}`} className="flex gap-2">
        <Input
          name="q"
          defaultValue={query}
          placeholder="제목으로 검색"
          aria-label="제목 검색"
          className="bg-background"
        />
        <Button type="submit" variant="outline" className="bg-background">
          <Search />
          검색
        </Button>
      </form>

      <p className="text-sm text-muted-foreground">
        {query ? <>&lsquo;{query}&rsquo; 검색 결과 </> : "전체 "}
        {total}건{totalPages > 1 && ` · ${current}/${totalPages} 페이지`}
        {query && (
          <>
            {" · "}
            <Link href={`/boards/${board.id}`} className="underline underline-offset-4">
              전체 보기
            </Link>
          </>
        )}
      </p>

      <Card className="py-0">
        <CardContent className="px-0">
          {posts.length === 0 ? (
            <p className="py-16 text-center text-muted-foreground">
              {query ? "검색 결과가 없습니다." : "아직 게시글이 없습니다. 첫 글을 남겨 보세요."}
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="hidden w-16 pl-4 text-center sm:table-cell">
                    번호
                  </TableHead>
                  <TableHead className="pl-4 sm:pl-2">제목</TableHead>
                  <TableHead className="hidden w-24 sm:table-cell">작성자</TableHead>
                  <TableHead className="hidden w-36 sm:table-cell">작성일</TableHead>
                  <TableHead className="hidden w-16 text-center sm:table-cell">조회</TableHead>
                  <TableHead className="hidden w-16 pr-4 text-center sm:table-cell">
                    하트
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {posts.map((post) => (
                  <TableRow key={post.id}>
                    <TableCell className="hidden pl-4 text-center text-muted-foreground sm:table-cell">
                      {post.id}
                    </TableCell>
                    <TableCell className="max-w-0 pl-4 sm:pl-2">
                      <Link
                        href={`/posts/${post.id}`}
                        className="flex items-center gap-1.5 font-medium hover:underline"
                      >
                        <span className="truncate">{post.title}</span>
                        {post.commentCount > 0 && (
                          <span className="flex shrink-0 items-center gap-0.5 text-xs font-semibold text-primary">
                            <MessageSquare className="size-3" />
                            {post.commentCount}
                          </span>
                        )}
                      </Link>
                      <span className="flex flex-wrap items-center gap-x-2 text-xs text-muted-foreground sm:hidden">
                        <span>{post.author}</span>
                        <span>{formatDate(post.createdAt)}</span>
                        <span className="flex items-center gap-0.5">
                          <Eye className="size-3" />
                          {post.views}
                        </span>
                        <span className="flex items-center gap-0.5">
                          <Heart className="size-3" />
                          {post.likeCount}
                        </span>
                      </span>
                    </TableCell>
                    <TableCell className="hidden truncate sm:table-cell">{post.author}</TableCell>
                    <TableCell className="hidden text-muted-foreground sm:table-cell">
                      {formatDate(post.createdAt)}
                    </TableCell>
                    <TableCell className="hidden text-center text-muted-foreground sm:table-cell">
                      {post.views}
                    </TableCell>
                    <TableCell className="hidden pr-4 text-center sm:table-cell">
                      <span
                        className={cn(
                          "inline-flex items-center gap-1",
                          post.likeCount > 0 ? "text-rose-500" : "text-muted-foreground",
                        )}
                      >
                        <Heart className={cn("size-3.5", post.likeCount > 0 && "fill-current")} />
                        {post.likeCount}
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {totalPages > 1 && (
        <Pagination current={current} totalPages={totalPages} href={pageHref} />
      )}
    </div>
  )
}

function Pagination({
  current,
  totalPages,
  href,
}: {
  current: number
  totalPages: number
  href: (page: number) => string
}) {
  // 현재 페이지 주변 최대 5개 번호만 보여준다
  const start = Math.max(1, Math.min(current - 2, totalPages - 4))
  const pages = Array.from({ length: Math.min(5, totalPages) }, (_, i) => start + i)

  return (
    <nav aria-label="페이지" className="flex flex-wrap items-center justify-center gap-1">
      <PageLink href={href(current - 1)} disabled={current === 1} label="이전 페이지">
        <ChevronLeft />
      </PageLink>
      {pages.map((p) => (
        <Link
          key={p}
          href={href(p)}
          aria-current={p === current ? "page" : undefined}
          className={buttonVariants({
            variant: p === current ? "default" : "outline",
            size: "icon",
          })}
        >
          {p}
        </Link>
      ))}
      <PageLink href={href(current + 1)} disabled={current === totalPages} label="다음 페이지">
        <ChevronRight />
      </PageLink>
    </nav>
  )
}

function PageLink({
  href,
  disabled,
  label,
  children,
}: {
  href: string
  disabled: boolean
  label: string
  children: React.ReactNode
}) {
  const className = buttonVariants({ variant: "ghost", size: "icon" })
  if (disabled) {
    return (
      <span aria-disabled className={cn(className, "opacity-40")}>
        {children}
      </span>
    )
  }
  return (
    <Link href={href} aria-label={label} className={className}>
      {children}
    </Link>
  )
}
