"use client"

import Link from "next/link"
import { useActionState } from "react"

import { createBoard } from "@/app/actions"
import { Field } from "@/components/post-form"
import { Button, buttonVariants } from "@/components/ui/button"
import { Card, CardContent, CardFooter } from "@/components/ui/card"
import { Input } from "@/components/ui/input"

export function BoardForm() {
  const [state, formAction, pending] = useActionState(createBoard, {})

  return (
    <form action={formAction}>
      <Card>
        <CardContent className="space-y-5">
          <Field id="name" label="게시판 이름" error={state.errors?.name}>
            <Input
              id="name"
              name="name"
              maxLength={30}
              defaultValue={state.values?.name}
              aria-invalid={!!state.errors?.name}
              placeholder="예: 교육 자료실"
            />
          </Field>
          <Field id="description" label="설명 (선택)" error={state.errors?.description}>
            <Input
              id="description"
              name="description"
              maxLength={200}
              defaultValue={state.values?.description}
              aria-invalid={!!state.errors?.description}
              placeholder="게시판을 한 줄로 소개해 주세요"
            />
          </Field>
        </CardContent>
        <CardFooter className="justify-end gap-2">
          <Link href="/" className={buttonVariants({ variant: "outline" })}>
            취소
          </Link>
          <Button type="submit" disabled={pending}>
            {pending ? "만드는 중…" : "게시판 만들기"}
          </Button>
        </CardFooter>
      </Card>
    </form>
  )
}
