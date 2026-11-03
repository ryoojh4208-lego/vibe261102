import "server-only"

import { db, iso } from "@/lib/db"

export type Board = {
  id: number
  name: string
  description: string
  postCount: number
  lastPostAt: string | null
}

export type BoardInput = Pick<Board, "name" | "description">

type Row = {
  id: number
  name: string
  description: string
  post_count: number
  last_post_at: Date | null
}

function toBoard(row: Row): Board {
  return {
    id: row.id,
    name: row.name,
    description: row.description,
    postCount: row.post_count,
    lastPostAt: iso(row.last_post_at),
  }
}

export async function listBoards() {
  const sql = await db()
  const rows = (await sql`
    SELECT b.id, b.name, b.description,
           count(p.id)::int AS post_count, max(p.created_at) AS last_post_at
    FROM boards b LEFT JOIN posts p ON p.board_id = b.id
    GROUP BY b.id
    ORDER BY b.id
  `) as Row[]
  return rows.map(toBoard)
}

export async function getBoard(id: number) {
  if (!Number.isInteger(id)) return null
  const sql = await db()
  const rows = (await sql`
    SELECT b.id, b.name, b.description,
           count(p.id)::int AS post_count, max(p.created_at) AS last_post_at
    FROM boards b LEFT JOIN posts p ON p.board_id = b.id
    WHERE b.id = ${id}
    GROUP BY b.id
  `) as Row[]
  return rows[0] ? toBoard(rows[0]) : null
}

export async function createBoard(input: BoardInput) {
  const sql = await db()
  const rows = (await sql`
    INSERT INTO boards (name, description)
    VALUES (${input.name}, ${input.description})
    RETURNING id
  `) as { id: number }[]
  return rows[0].id
}

export async function deleteBoard(id: number) {
  const sql = await db()
  await sql`DELETE FROM boards WHERE id = ${id}`
}
