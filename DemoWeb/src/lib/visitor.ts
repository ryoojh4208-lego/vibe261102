import "server-only"

import { cookies } from "next/headers"

const COOKIE = "visitor_id"

/** 하트 중복 방지용 방문자 ID. 쿠키가 없으면 undefined */
export async function getVisitorId() {
  return (await cookies()).get(COOKIE)?.value
}

/** Server Action 안에서만 호출: 방문자 ID가 없으면 새로 발급해 쿠키에 저장 */
export async function ensureVisitorId() {
  const store = await cookies()
  const existing = store.get(COOKIE)?.value
  if (existing) return existing
  const id = crypto.randomUUID()
  store.set(COOKIE, id, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 365,
  })
  return id
}
