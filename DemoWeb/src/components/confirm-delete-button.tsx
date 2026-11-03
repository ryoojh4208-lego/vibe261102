"use client"

import { useTransition } from "react"
import { Trash2 } from "lucide-react"

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"

type Props = {
  /** 확인 버튼을 누르면 실행할 Server Action (인자는 bind로 미리 넣어 둔다) */
  action: () => Promise<void>
  title: string
  description: string
  label?: string
  size?: "default" | "sm" | "xs"
}

export function ConfirmDeleteButton({
  action,
  title,
  description,
  label = "삭제",
  size = "default",
}: Props) {
  const [pending, startTransition] = useTransition()

  return (
    <AlertDialog>
      <AlertDialogTrigger render={<Button variant="destructive" size={size} />}>
        <Trash2 />
        {label}
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          <AlertDialogDescription>{description}</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>취소</AlertDialogCancel>
          <AlertDialogAction
            variant="destructive"
            disabled={pending}
            onClick={() => startTransition(() => action())}
          >
            {pending ? "삭제 중…" : "삭제"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
