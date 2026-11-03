import Link from "next/link"
import { notFound } from "next/navigation"
import { Suspense } from "react"
import { ArrowLeft, Pencil } from "lucide-react"

import { DeletePostButton } from "@/components/delete-post-button"
import { buttonVariants } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { formatDate } from "@/lib/format"
import { getPost } from "@/lib/posts"

export default function PostPage({ params }: PageProps<"/posts/[id]">) {
  return (
    <Suspense fallback={<p className="text-muted-foreground">불러오는 중…</p>}>
      <PostDetail params={params} />
    </Suspense>
  )
}

async function PostDetail({ params }: Pick<PageProps<"/posts/[id]">, "params">) {
  const { id } = await params
  const post = await getPost(Number(id))
  if (!post) notFound()

  const edited = post.updatedAt !== post.createdAt

  return (
    <div className="space-y-4">
      <Link href="/" className={buttonVariants({ variant: "ghost", size: "sm" })}>
        <ArrowLeft />
        목록으로
      </Link>
      <Card>
        <CardHeader className="border-b">
          <CardTitle className="text-xl break-words">{post.title}</CardTitle>
          <CardDescription>
            {post.author} · {formatDate(post.createdAt)}
            {edited && <> · 수정됨 {formatDate(post.updatedAt)}</>}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="min-h-32 leading-7 break-words whitespace-pre-wrap">
            {post.content}
          </p>
        </CardContent>
        <CardFooter className="justify-end gap-2 border-t">
          <Link
            href={`/posts/${post.id}/edit`}
            className={buttonVariants({ variant: "outline" })}
          >
            <Pencil />
            수정
          </Link>
          <DeletePostButton id={post.id} title={post.title} />
        </CardFooter>
      </Card>
    </div>
  )
}
