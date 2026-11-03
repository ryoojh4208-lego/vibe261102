"use client"

import { useOptimistic, useTransition } from "react"
import { Heart } from "lucide-react"

import { toggleLike } from "@/app/actions"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export function LikeButton({
  postId,
  liked,
  count,
}: {
  postId: number
  liked: boolean
  count: number
}) {
  const [, startTransition] = useTransition()
  // 서버 응답을 기다리지 않고 바로 하트를 채우거나 비운다
  const [state, setOptimistic] = useOptimistic(
    { liked, count },
    (s) => ({ liked: !s.liked, count: s.count + (s.liked ? -1 : 1) }),
  )

  return (
    <Button
      variant="outline"
      aria-pressed={state.liked}
      aria-label={state.liked ? "하트 취소" : "하트 누르기"}
      className={cn(state.liked && "border-rose-300 bg-rose-50 text-rose-600 hover:bg-rose-100")}
      onClick={() =>
        startTransition(async () => {
          setOptimistic(null)
          await toggleLike(postId)
        })
      }
    >
      <Heart className={cn(state.liked && "fill-current")} />
      {state.count}
    </Button>
  )
}
