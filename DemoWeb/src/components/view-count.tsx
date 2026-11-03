"use client"

import { useEffect, useRef, useState } from "react"
import { Eye } from "lucide-react"

import { recordView } from "@/app/actions"

/**
 * 화면이 열릴 때 조회수를 1 올리고 올라간 값을 보여준다.
 * 서버 렌더링 중에 올리면 하트·댓글로 화면이 다시 그려질 때마다 조회수가 늘어나므로
 * 브라우저에서 한 번만 호출한다.
 */
export function ViewCount({ postId, initial }: { postId: number; initial: number }) {
  const [views, setViews] = useState(initial)
  const recorded = useRef(false)

  useEffect(() => {
    if (recorded.current) return
    recorded.current = true
    recordView(postId).then((next) => {
      if (next !== null) setViews(next)
    })
  }, [postId])

  return (
    <span className="inline-flex items-center gap-1" title="조회수">
      <Eye className="size-4" />
      조회 {views}
    </span>
  )
}
