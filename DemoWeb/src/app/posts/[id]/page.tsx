import Link from "next/link"
import { notFound } from "next/navigation"
import { Suspense } from "react"
import { ArrowLeft, MessageSquare, Pencil } from "lucide-react"

import { deleteComment, deletePost } from "@/app/actions"
import { CommentForm } from "@/components/comment-form"
import { ConfirmDeleteButton } from "@/components/confirm-delete-button"
import { LikeButton } from "@/components/like-button"
import { buttonVariants } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { ViewCount } from "@/components/view-count"
import { listComments } from "@/lib/comments"
import { formatDate } from "@/lib/format"
import { getPost } from "@/lib/posts"
import { getVisitorId } from "@/lib/visitor"

export default function PostPage({ params }: PageProps<"/posts/[id]">) {
  return (
    <Suspense fallback={<p className="text-muted-foreground">불러오는 중…</p>}>
      <PostDetail params={params} />
    </Suspense>
  )
}

async function PostDetail({ params }: Pick<PageProps<"/posts/[id]">, "params">) {
  const { id } = await params
  const post = await getPost(Number(id), await getVisitorId())
  if (!post) notFound()
  const comments = await listComments(post.id)

  const edited = post.updatedAt !== post.createdAt

  return (
    <div className="space-y-4">
      <Link
        href={`/boards/${post.boardId}`}
        className={buttonVariants({ variant: "ghost", size: "sm" })}
      >
        <ArrowLeft />
        {post.boardName}
      </Link>

      <Card>
        <CardHeader className="border-b">
          <CardTitle className="text-xl break-words">{post.title}</CardTitle>
          <CardDescription className="flex flex-wrap items-center gap-x-3 gap-y-1">
            <span>
              {post.author} · {formatDate(post.createdAt)}
              {edited && <> · 수정됨 {formatDate(post.updatedAt)}</>}
            </span>
            <ViewCount postId={post.id} initial={post.views} />
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="min-h-32 leading-7 break-words whitespace-pre-wrap">{post.content}</p>
        </CardContent>
        <CardFooter className="flex-wrap justify-between gap-2 border-t">
          <LikeButton postId={post.id} liked={post.liked} count={post.likeCount} />
          <div className="flex gap-2">
            <Link
              href={`/posts/${post.id}/edit`}
              className={buttonVariants({ variant: "outline" })}
            >
              <Pencil />
              수정
            </Link>
            <ConfirmDeleteButton
              action={deletePost.bind(null, post.id)}
              title="게시글을 삭제할까요?"
              description={`'${post.title}' 글과 댓글이 영구히 삭제되며 되돌릴 수 없습니다.`}
            />
          </div>
        </CardFooter>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <MessageSquare className="size-4" />
            댓글 {comments.length}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {comments.length > 0 && (
            <ul className="divide-y rounded-lg border">
              {comments.map((comment) => (
                <li key={comment.id} className="flex gap-3 p-3">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm">
                      <span className="font-medium">{comment.author}</span>
                      <span className="ml-2 text-xs text-muted-foreground">
                        {formatDate(comment.createdAt)}
                      </span>
                    </p>
                    <p className="mt-1 text-sm leading-6 break-words whitespace-pre-wrap">
                      {comment.content}
                    </p>
                  </div>
                  <ConfirmDeleteButton
                    action={deleteComment.bind(null, comment.id)}
                    title="댓글을 삭제할까요?"
                    description="삭제한 댓글은 되돌릴 수 없습니다."
                    size="xs"
                  />
                </li>
              ))}
            </ul>
          )}
          <CommentForm postId={post.id} />
        </CardContent>
      </Card>
    </div>
  )
}
