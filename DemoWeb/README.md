# DemoWeb 게시판

Next.js(App Router) + TypeScript + shadcn/ui로 만든 간단한 웹 게시판입니다.

## 기능

- 게시글 목록 (최신순, 10개씩 페이지네이션)
- 제목 검색
- 게시글 상세 보기
- 게시글 작성 / 수정 / 삭제 (제목, 작성자, 내용) — 입력값 검증, 삭제 전 확인 대화상자
- 반응형 레이아웃 (모바일에서는 번호·작성자·작성일 열을 제목 아래로 접어서 표시)

## 실행

```bash
npm install
npm run dev -- -p 3100   # http://localhost:3100
```

프로덕션 빌드: `npm run build && npm start`

## 데이터 저장 방식: 로컬 JSON 파일 + Server Actions

글은 `data/posts.json` 한 파일에 저장되고, 읽기는 서버 컴포넌트에서, 쓰기(작성·수정·삭제)는 Server Actions(`src/app/actions.ts`)에서 처리합니다. 파일이 없으면 첫 실행 때 안내 글 1개로 자동 생성됩니다.

이 방식을 고른 이유:

- **설치 없이 바로 실행** — DB 서버가 필요 없고, SQLite처럼 Windows에서 네이티브 모듈을 빌드할 일도 없습니다.
- **눈으로 확인 가능** — 저장된 데이터를 메모장으로 열어 바로 볼 수 있어 학습·연습용으로 적합합니다.
- **교체가 쉬움** — 데이터 접근은 `src/lib/posts.ts` 한 곳에 모여 있어, 나중에 SQLite나 실제 DB로 바꿀 때 이 파일만 고치면 됩니다.

한계: 한 서버 프로세스에서만 쓰는 연습용 방식입니다. 쓰기는 프로세스 안에서 순서대로 처리하고 임시 파일로 교체해 파일이 깨지지 않게 했지만, 여러 서버를 띄우거나 Vercel 같은 서버리스 환경에 배포하면 데이터가 유지되지 않습니다.

## 폴더 구조

```
src/
  app/
    page.tsx                 목록 + 검색 + 페이지네이션
    posts/new/page.tsx       글쓰기
    posts/[id]/page.tsx      상세 보기 (수정·삭제 버튼)
    posts/[id]/edit/page.tsx 글 수정
    actions.ts               Server Actions (작성·수정·삭제)
  components/
    post-form.tsx            작성/수정 공용 폼
    delete-post-button.tsx   삭제 확인 대화상자
    ui/                      shadcn/ui 컴포넌트
  lib/posts.ts               JSON 파일 저장소
data/posts.json              게시글 데이터 (git에는 올리지 않음)
```
