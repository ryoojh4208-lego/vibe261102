import Link from "next/link"

import { buttonVariants } from "@/components/ui/button"

export default function NotFound() {
  return (
    <div className="space-y-4 py-16 text-center">
      <h1 className="text-2xl font-bold">게시글을 찾을 수 없습니다</h1>
      <p className="text-muted-foreground">삭제되었거나 존재하지 않는 글입니다.</p>
      <Link href="/" className={buttonVariants({ variant: "outline" })}>
        목록으로
      </Link>
    </div>
  )
}
