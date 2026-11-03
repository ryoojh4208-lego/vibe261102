import { createPost } from "@/app/actions"
import { PostForm } from "@/components/post-form"

export const metadata = { title: "글쓰기" }

export default function NewPostPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold tracking-tight">글쓰기</h1>
      <PostForm action={createPost} submitLabel="등록" cancelHref="/" />
    </div>
  )
}
