"use client"

import { useActionState } from "react"

import { addComment } from "@/app/actions"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"

export function CommentForm({ postId }: { postId: number }) {
  const [state, formAction, pending] = useActionState(addComment.bind(null, postId), {})

  return (
    <form action={formAction} className="space-y-2">
      <Input
        name="author"
        maxLength={30}
        defaultValue={state.values?.author}
        aria-label="작성자"
        aria-invalid={!!state.errors?.author}
        placeholder="이름"
        className="sm:max-w-xs"
      />
      <Textarea
        name="content"
        maxLength={1000}
        rows={3}
        defaultValue={state.values?.content}
        aria-label="댓글"
        aria-invalid={!!state.errors?.content}
        placeholder="댓글을 남겨 주세요"
      />
      {(state.errors?.author || state.errors?.content) && (
        <p className="text-sm text-destructive">
          {state.errors.author ?? state.errors.content}
        </p>
      )}
      <div className="flex justify-end">
        <Button type="submit" disabled={pending}>
          {pending ? "등록 중…" : "댓글 등록"}
        </Button>
      </div>
    </form>
  )
}
