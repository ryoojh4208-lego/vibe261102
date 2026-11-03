import Link from "next/link"
import { Suspense } from "react"
import { Search } from "lucide-react"

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
import { formatDate } from "@/lib/format"
import { listPosts } from "@/lib/posts"

export default function Home({ searchParams }: PageProps<"/">) {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold tracking-tight">게시글 목록</h1>
      <Suspense fallback={<p className="text-muted-foreground">불러오는 중…</p>}>
        <PostList searchParams={searchParams} />
      </Suspense>
    </div>
  )
}

async function PostList({ searchParams }: Pick<PageProps<"/">, "searchParams">) {
  const params = await searchParams
  const query = typeof params.q === "string" ? params.q : ""
  const page = Number(params.page) || 1
  const { posts, total, totalPages, page: current } = await listPosts({ query, page })

  const pageHref = (p: number) => {
    const sp = new URLSearchParams()
    if (query) sp.set("q", query)
    if (p > 1) sp.set("page", String(p))
    const s = sp.toString()
    return s ? `/?${s}` : "/"
  }

  return (
    <>
      <form action="/" className="flex gap-2">
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
        {total}건
        {query && (
          <>
            {" · "}
            <Link href="/" className="underline underline-offset-4">
              전체 보기
            </Link>
          </>
        )}
      </p>

      <Card className="py-0">
        <CardContent className="px-0">
          {posts.length === 0 ? (
            <p className="py-16 text-center text-muted-foreground">
              {query ? "검색 결과가 없습니다." : "아직 게시글이 없습니다."}
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="hidden w-16 pl-4 text-center sm:table-cell">
                    번호
                  </TableHead>
                  <TableHead className="pl-4 sm:pl-2">제목</TableHead>
                  <TableHead className="hidden w-28 sm:table-cell">작성자</TableHead>
                  <TableHead className="hidden w-40 pr-4 sm:table-cell">작성일</TableHead>
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
                        className="block truncate font-medium hover:underline"
                      >
                        {post.title}
                      </Link>
                      <span className="text-xs text-muted-foreground sm:hidden">
                        {post.author} · {formatDate(post.createdAt)}
                      </span>
                    </TableCell>
                    <TableCell className="hidden truncate sm:table-cell">
                      {post.author}
                    </TableCell>
                    <TableCell className="hidden pr-4 text-muted-foreground sm:table-cell">
                      {formatDate(post.createdAt)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {totalPages > 1 && (
        <nav aria-label="페이지" className="flex flex-wrap justify-center gap-1">
          {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
            <Link
              key={p}
              href={pageHref(p)}
              aria-current={p === current ? "page" : undefined}
              className={buttonVariants({
                variant: p === current ? "default" : "outline",
                size: "icon",
              })}
            >
              {p}
            </Link>
          ))}
        </nav>
      )}
    </>
  )
}
