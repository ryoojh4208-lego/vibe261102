import { BoardForm } from "@/components/board-form"

export const metadata = { title: "게시판 만들기" }

export default function NewBoardPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold tracking-tight">게시판 만들기</h1>
      <BoardForm />
    </div>
  )
}
