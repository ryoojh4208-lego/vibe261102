import "server-only"

import { promises as fs } from "fs"
import path from "path"

export type Post = {
  id: number
  title: string
  author: string
  content: string
  createdAt: string
  updatedAt: string
}

export type PostInput = Pick<Post, "title" | "author" | "content">

const DATA_FILE = path.join(process.cwd(), "data", "posts.json")

const SEED: Post[] = [
  {
    id: 1,
    title: "게시판에 오신 것을 환영합니다",
    author: "관리자",
    content:
      "DemoWeb 게시판입니다.\n상단의 '글쓰기' 버튼으로 새 글을 작성하고, 글 상세 화면에서 수정·삭제할 수 있습니다.",
    createdAt: "2026-11-03T00:00:00.000Z",
    updatedAt: "2026-11-03T00:00:00.000Z",
  },
]

async function readAll(): Promise<Post[]> {
  try {
    const raw = await fs.readFile(DATA_FILE, "utf8")
    return JSON.parse(raw) as Post[]
  } catch (err) {
    // 파일이 없으면 샘플 글로 시작하고, 첫 쓰기 때 파일이 만들어진다
    if ((err as NodeJS.ErrnoException).code === "ENOENT") {
      return structuredClone(SEED)
    }
    throw err
  }
}

async function writeAll(posts: Post[]) {
  await fs.mkdir(path.dirname(DATA_FILE), { recursive: true })
  // 임시 파일에 쓴 뒤 교체해서 쓰기 도중 파일이 깨지지 않게 한다
  const tmp = `${DATA_FILE}.${process.pid}.tmp`
  await fs.writeFile(tmp, JSON.stringify(posts, null, 2), "utf8")
  await fs.rename(tmp, DATA_FILE)
}

// 동시에 들어온 쓰기 요청을 한 줄로 세워 서로 덮어쓰지 않게 한다
let queue: Promise<unknown> = Promise.resolve()
function mutate<T>(fn: (posts: Post[]) => Promise<T> | T): Promise<T> {
  const run = queue.then(async () => {
    const posts = await readAll()
    const result = await fn(posts)
    await writeAll(posts)
    return result
  })
  queue = run.catch(() => {})
  return run
}

export async function listPosts({
  query = "",
  page = 1,
  pageSize = 10,
}: {
  query?: string
  page?: number
  pageSize?: number
}) {
  const q = query.trim().toLowerCase()
  const filtered = (await readAll())
    .filter((p) => !q || p.title.toLowerCase().includes(q))
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt) || b.id - a.id)

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize))
  const current = Math.min(Math.max(1, page), totalPages)
  return {
    posts: filtered.slice((current - 1) * pageSize, current * pageSize),
    total: filtered.length,
    page: current,
    totalPages,
  }
}

export async function getPost(id: number) {
  return (await readAll()).find((p) => p.id === id) ?? null
}

export function createPost(input: PostInput) {
  return mutate((posts) => {
    const now = new Date().toISOString()
    const post: Post = {
      id: posts.reduce((max, p) => Math.max(max, p.id), 0) + 1,
      ...input,
      createdAt: now,
      updatedAt: now,
    }
    posts.push(post)
    return post
  })
}

export function updatePost(id: number, input: PostInput) {
  return mutate((posts) => {
    const post = posts.find((p) => p.id === id)
    if (!post) return null
    Object.assign(post, input, { updatedAt: new Date().toISOString() })
    return post
  })
}

export function deletePost(id: number) {
  return mutate((posts) => {
    const index = posts.findIndex((p) => p.id === id)
    if (index === -1) return false
    posts.splice(index, 1)
    return true
  })
}
