"use client"

import Link from "next/link"
import { useActionState } from "react"

import type { FormState } from "@/app/actions"
import { Button, buttonVariants } from "@/components/ui/button"
import { Card, CardContent, CardFooter } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"

type PostFormState = FormState<"title" | "author" | "content">

type Props = {
  action: (state: PostFormState, formData: FormData) => Promise<PostFormState>
  defaultValues?: { title: string; author: string; content: string }
  submitLabel: string
  cancelHref: string
}

export function PostForm({ action, defaultValues, submitLabel, cancelHref }: Props) {
  const [state, formAction, pending] = useActionState(action, {})
  const values = state.values ?? defaultValues

  return (
    <form action={formAction}>
      <Card>
        <CardContent className="space-y-5">
          <Field id="title" label="제목" error={state.errors?.title}>
            <Input
              id="title"
              name="title"
              maxLength={100}
              defaultValue={values?.title}
              aria-invalid={!!state.errors?.title}
              placeholder="제목을 입력하세요"
            />
          </Field>
          <Field id="author" label="작성자" error={state.errors?.author}>
            <Input
              id="author"
              name="author"
              maxLength={30}
              defaultValue={values?.author}
              aria-invalid={!!state.errors?.author}
              placeholder="이름"
              className="sm:max-w-xs"
            />
          </Field>
          <Field id="content" label="내용" error={state.errors?.content}>
            <Textarea
              id="content"
              name="content"
              rows={12}
              className="min-h-60"
              defaultValue={values?.content}
              aria-invalid={!!state.errors?.content}
              placeholder="내용을 입력하세요"
            />
          </Field>
        </CardContent>
        <CardFooter className="justify-end gap-2">
          <Link href={cancelHref} className={buttonVariants({ variant: "outline" })}>
            취소
          </Link>
          <Button type="submit" disabled={pending}>
            {pending ? "저장 중…" : submitLabel}
          </Button>
        </CardFooter>
      </Card>
    </form>
  )
}

export function Field({
  id,
  label,
  error,
  children,
}: {
  id: string
  label: string
  error?: string
  children: React.ReactNode
}) {
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>{label}</Label>
      {children}
      {error && <p className="text-sm text-destructive">{error}</p>}
    </div>
  )
}
