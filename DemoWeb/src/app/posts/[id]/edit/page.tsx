import { notFound } from "next/navigation"
import { Suspense } from "react"

import { updatePost } from "@/app/actions"
import { PostForm } from "@/components/post-form"
import { getPost } from "@/lib/posts"

export const metadata = { title: "글 수정" }

export default function EditPostPage({ params }: PageProps<"/posts/[id]/edit">) {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold tracking-tight">글 수정</h1>
      <Suspense fallback={<p className="text-muted-foreground">불러오는 중…</p>}>
        <EditForm params={params} />
      </Suspense>
    </div>
  )
}

async function EditForm({ params }: Pick<PageProps<"/posts/[id]/edit">, "params">) {
  const { id } = await params
  const post = await getPost(Number(id))
  if (!post) notFound()

  return (
    <PostForm
      action={updatePost.bind(null, post.id)}
      defaultValues={post}
      submitLabel="수정 완료"
      cancelHref={`/posts/${post.id}`}
    />
  )
}
