import { notFound } from "next/navigation"
import { Suspense } from "react"

import { createPost } from "@/app/actions"
import { PostForm } from "@/components/post-form"
import { getBoard } from "@/lib/boards"

export const metadata = { title: "글쓰기" }

export default function NewPostPage({ params }: PageProps<"/boards/[boardId]/new">) {
  return (
    <Suspense fallback={<p className="text-muted-foreground">불러오는 중…</p>}>
      <NewPost params={params} />
    </Suspense>
  )
}

async function NewPost({ params }: Pick<PageProps<"/boards/[boardId]/new">, "params">) {
  const { boardId } = await params
  const board = await getBoard(Number(boardId))
  if (!board) notFound()

  return (
    <div className="space-y-4">
      <div>
        <p className="text-sm text-muted-foreground">{board.name}</p>
        <h1 className="text-2xl font-bold tracking-tight">글쓰기</h1>
      </div>
      <PostForm
        action={createPost.bind(null, board.id)}
        submitLabel="등록"
        cancelHref={`/boards/${board.id}`}
      />
    </div>
  )
}
