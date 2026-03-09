# CLAUDE.md — 범용 프로젝트 템플릿

> 새 프로젝트에 복사하여 `[프로젝트명]`, `[설명]` 등을 교체하세요.
> 이 템플릿은 Sentimind 프로젝트(127+ 커밋)에서 검증된 패턴을 일반화한 것입니다.

---

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

[프로젝트명] — [한 줄 설명]

## Commands

- **서버 실행**: `node server.js` (http://localhost:3000)
- **의존성 설치**: `npm install`
- **테스트**: `npm test`

## Architecture

```
public/              ──fetch──▸  server.js (Express)  ──fetch──▸  External API
├── index.html                        │
├── css/                         config/
├── js/ (ES modules)             lib/
└── sw.js                        routes/
```

[여기에 프로젝트 고유 아키텍처 다이어그램 작성]

## Environment Variables (.env)

```bash
# 필수
API_KEY=                    # 외부 API 키
SUPABASE_URL=               # Supabase 프로젝트 URL
SUPABASE_ANON_KEY=          # Supabase 공개 키
SUPABASE_SERVICE_ROLE_KEY=  # Supabase 서비스 키 (서버 전용)

# 선택 (기본값 있음)
NODE_ENV=production
LOG_LEVEL=INFO
SLOW_REQUEST_MS=3000
```

---

## Core Principles

### 1. Simplicity First
- 가장 간단한 방법으로 구현. 최소한의 코드만 변경
- 근본 원인을 찾아 수정. 임시 해결책 금지
- 필요한 부분만 수정. 불필요한 리팩토링 하지 않기

### 2. Configuration External
- **모든 설정값은 코드 외부에서 관리** (환경변수, 설정파일)
- ✅ `const MODEL = process.env.MODEL || 'default-model'`
- ❌ `const MODEL = 'hard-coded-model'`
- 숫자형: `parseInt(process.env.X || '기본값', 10)`
- config/ 디렉토리에 설정 파일 분리

### 3. Documentation Sync
- 기능 추가/변경 시 아래 문서를 **반드시 함께 업데이트**:
  - `README.md` — 기능 목록, API, 프로젝트 구조
  - `CLAUDE.md` — 아키텍처, 기술 결정, 파일 구조
  - `docs/API.md` — API 엔드포인트 변경 시
  - `docs/DEVLOG.md` — 커밋/기능 완료 시 개발목록 업데이트
- 커밋에 문서 변경도 같이 포함

### 4. Frequent Commits
- 작업 내용을 수시로 커밋
- push는 사용자에게 확인 후 진행

---

## Workflow Orchestration

### Plan First
- 3+ 단계 또는 설계 결정이 필요한 작업은 반드시 계획 먼저
- 잘못된 방향이면 즉시 멈추고 재계획
- `tasks/todo.md`에 체크 가능한 항목으로 계획 작성

### Subagent Strategy
- 서브에이전트를 적극 활용하여 메인 컨텍스트 깨끗하게 유지
- 리서치, 탐색, 병렬 분석은 서브에이전트에 위임
- 복잡한 문제는 서브에이전트로 더 많은 계산 투입

### Self-Improvement Loop
- 사용자 교정 후: `tasks/lessons.md`에 패턴 기록
- 같은 실수 반복 방지 규칙 작성
- 세션 시작 시 lessons.md 검토

### Verification Before Done
- 작업 완료 전 반드시 동작 증명 (테스트, 로그, 서버 실행)
- "staff engineer가 승인할 수준인가?" 자문
- 테스트 실행, 로그 확인, 정확성 입증

### Autonomous Bug Fixing
- 버그 리포트 받으면 바로 수정. 질문하지 않기
- 로그, 에러, 실패 테스트를 찾아서 해결
- 사용자의 컨텍스트 전환 불필요

---

## Task Management

1. **Plan First**: `tasks/todo.md`에 체크 가능 항목으로 계획
2. **Verify Plan**: 구현 전 계획 확인
3. **Track Progress**: 진행하면서 항목 완료 표시
4. **Explain Changes**: 각 단계에서 고수준 요약
5. **Document Results**: `tasks/todo.md`에 리뷰 섹션 추가
6. **Capture Lessons**: 교정 후 `tasks/lessons.md` 업데이트

---

## Git Commit Convention

### 형식
```
<타입>(<범위>): <한국어 설명 35자 이내>

<본문 - 선택적, 한국어>

<꼬리말 - 선택적>
```

### 규칙
- **타입, scope**: 영어 소문자
- **설명 (제목), 본문**: 한국어
- **마침표, 이모지**: 금지

### 타입 목록

| 타입 | 용도 |
|------|------|
| `feat` | 새로운 기능 추가 |
| `fix` | 버그 수정 |
| `docs` | 문서만 변경 |
| `style` | 코드 포맷/스타일만 변경 |
| `refactor` | 리팩토링 (기능/버그 변경 없음) |
| `test` | 테스트 추가/수정 |
| `chore` | 빌드, 설정, 패키지 변경 |
| `data` | 스키마, 마이그레이션 |
| `infra` | 서버 설정, 환경변수, 배포 |

### Scope 목록 (선택적)

`api` · `server` · `frontend` · `data` · `db` · `auth` · `config` · `ci`

### 예시

**Good ✅**
```
feat(api): 감정 분석 엔드포인트 추가
fix(frontend): 검색 필터 버그 수정
refactor(server): 라우트 모듈 분리
```

**Bad ❌**
```
update code.           # 마침표, 모호함
Add new stuff          # 타입 없음
Feat(API): Added       # 영문 설명
```

---

## Backend Patterns

### Express 서버 구조

**라우트 모듈 분리 (Dependency Injection)**
```javascript
// server.js — 의존성 조립 후 주입
const routeDeps = { logger, db, dbAdmin, authMiddleware, optionalAuth, config, validators };
app.use('/api/auth', require('./routes/auth')(routeDeps));

// routes/auth.js — 필요한 것만 구조분해
module.exports = function(deps) {
  const { logger, db, validators: { validateEmail } } = deps;
  const router = express.Router();
  // ...
  return router;
};
```

**미들웨어 순서**
```
1. helmet (보안 헤더)
2. cors
3. express.json({ limit: '10kb' })
4. express.static('public/')        ← public/ 디렉토리만 서빙
5. API 요청 로깅 미들웨어           ← 자동 requestId + 응답 시간
6. 라우트 (rate limiter → auth → handler)
7. /api 404 핸들러
8. 글로벌 에러 핸들러 (err, req, res, next)
```

### 인증 패턴

**authMiddleware + optionalAuth 이중 구조**
```javascript
// 필수 인증: 토큰 없으면 401
router.post('/entries', authMiddleware, handler);

// 선택 인증: 게스트도 허용 (req.user = null)
router.post('/analyze', optionalAuth, handler);

// 핸들러에서 분기
if (req.user) { /* 회원 로직 */ }
else { /* 게스트 로직 */ }
```

**토큰 만료 vs 변조 구분**
```javascript
const code = isExpired ? 'AUTH_TOKEN_EXPIRED' : 'AUTH_TOKEN_INVALID';
// → 클라이언트가 refresh 여부 판단 가능
```

### 보안 체크리스트
- [ ] `express.static`은 `public/`만 서빙 (서버 코드, .env 노출 방지)
- [ ] `express.json({ limit: '10kb' })` payload 크기 제한
- [ ] Rate limiter: 엔드포인트별 세분화 (auth 엄격, 읽기 완화)
- [ ] CSP: `scriptSrc: ["'self'"]` (unsafe-inline 금지)
- [ ] XSS: `escapeHtml()` — `&`, `<`, `>`, `"`, `'` 5가지 이스케이프
- [ ] CSV export: 수식 주입 방지 (`=`, `+`, `-`, `@` 시작 시 `'` 접두)
- [ ] PII(이메일) 로그 마스킹: `j***n@example.com`
- [ ] 보안 이벤트 전용 로거 (`[SECURITY]` 접두)
- [ ] 비밀번호 재설정: 항상 동일 응답 (이메일 열거 공격 방지)

### 에러 응답 형식 통일
```javascript
// 항상 { error: 메시지, code: 머신코드 }
res.status(400).json({ error: '사람이 읽을 수 있는 메시지', code: 'VALIDATION_ERROR' });
res.status(401).json({ error: '...', code: 'AUTH_TOKEN_EXPIRED' });
res.status(429).json({ error: '...', code: 'RATE_LIMITED' });
res.status(500).json({ error: '...', code: 'INTERNAL_ERROR' });
```

### 입력 검증 패턴
```javascript
// 모든 검증 함수: { valid, error?, value? } 반환
function validateField(value) {
  if (!value) return { valid: false, error: '필드를 입력해주세요.' };
  return { valid: true, value: value.trim() };
}

// 라우트에서 early return
const v = validateField(req.body.field);
if (!v.valid) return res.status(400).json({ error: v.error, code: 'VALIDATION_ERROR' });
// 이후 v.value 사용 (정제된 안전한 값)
```

### Soft Delete + Pagination
```javascript
// 삭제: deleted_at 타임스탬프
await db.from('items').update({ deleted_at: new Date().toISOString() }).eq('id', id);

// 조회: 항상 deleted_at IS NULL (RLS에서도 강제)
.is('deleted_at', null)

// Pagination: 범위 강제
const limit = Math.min(Math.max(parseInt(query.limit) || 20, 1), 100);
const offset = Math.max(parseInt(query.offset) || 0, 0);
```

---

## Logging System

### 환경별 분리
```javascript
if (IS_PRODUCTION) {
  // 서버리스: 구조화 JSON만 (ANSI 없음)
  console.log(JSON.stringify({ timestamp, level, message, data }));
} else {
  // 로컬: 컬러 콘솔 + 일별 파일 로테이션
  console.log(`${COLOR[level]}[${level}] ${message}\x1b[0m`);
  appendFile(dailyLogFile, JSON.stringify(logEntry));
}
```

### 글로벌 요청 로깅 미들웨어
```javascript
app.use('/api', (req, res, next) => {
  req.rid = generateRequestId();
  res.set('X-Request-Id', req.rid);
  const start = Date.now();

  res.on('finish', () => {
    const duration = Date.now() - start;
    const logData = { requestId: req.rid, method: req.method, path: req.originalUrl,
                      status: res.statusCode, duration: `${duration}ms`, userId: req.user?.id };
    if (duration >= SLOW_REQUEST_MS) logger.warn('느린 요청', logData);
    else logger.info('API 요청', logData);
  });
  next();
});
```

### 체크리스트
- [ ] 모든 로그에 `requestId` 포함
- [ ] `X-Request-Id` 응답 헤더 (클라이언트 디버깅)
- [ ] `SLOW_REQUEST_MS` 환경변수 (기본 3000ms)
- [ ] 프로덕션: 스택 트레이스 제외
- [ ] 글로벌 에러 핸들러에 method/path/userId 포함

---

## Supabase Patterns

### 3가지 클라이언트 분리
```javascript
const publicClient = createClient(URL, ANON_KEY);      // 인증 전 (signup/login)
const adminClient  = createClient(URL, SERVICE_KEY);    // RLS 우회 (서버 전용)
const userClient   = createClient(URL, ANON_KEY, {      // RLS 적용 (사용자 데이터)
  global: { headers: { Authorization: `Bearer ${jwt}` } }
});
```

### RLS 정책 원칙
```sql
-- 모든 테이블에 RLS 활성화
ALTER TABLE public.items ENABLE ROW LEVEL SECURITY;

-- SELECT: 자기 데이터 + soft delete 필터
CREATE POLICY "select_own" ON public.items FOR SELECT
  USING (auth.uid() = user_id AND deleted_at IS NULL);

-- INSERT: 자기 user_id만
CREATE POLICY "insert_own" ON public.items FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- service_role은 RLS를 우회하므로 INSERT 정책 불필요
-- WITH CHECK (true) 사용 금지 (보안 위험)
```

### 마이그레이션 파일 규칙
```
migrations/
  001_create_tables.sql       # 테이블
  002_create_indexes.sql      # 인덱스
  003_create_rls_policies.sql # RLS
  004_create_triggers.sql     # 트리거
  005_add_new_column.sql      # 점진적 스키마 변경
```
- 3자리 순번 + snake_case
- `CREATE IF NOT EXISTS` 멱등성 보장
- 한 파일에 하나의 변경만

---

## LLM API Integration

### 재시도 + 지수 백오프
```javascript
async function callLLMAPI(requestBody) {
  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    const response = await fetch(url, { signal: AbortSignal.timeout(TIMEOUT_MS) });

    if (response.status === 429 && attempt < MAX_RETRIES) {
      await sleep(BASE_DELAY * Math.pow(2, attempt) * (1 + Math.random() * 0.1));
      continue;  // 429만 재시도
    }
    if (response.status === 400 || response.status === 403) throw new Error();  // 즉시 실패
    // ...
  }
}
```

### LLM 응답 파싱 (방어적)
```javascript
function parseLLMResponse(text) {
  let json = text.trim();
  // ```json ... ``` 래핑 제거
  const codeBlock = json.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (codeBlock) json = codeBlock[1].trim();

  const parsed = JSON.parse(json);
  // 모든 필드 타입 검증 + 기본값 (LLM 출력은 신뢰 불가)
  return {
    field: typeof parsed.field === 'string' ? parsed.field : 'default',
  };
}
```

### 토큰 비용 추적
```javascript
logger.info('LLM 호출 완료', {
  requestId: rid, duration: `${ms}ms`,
  tokens: { input, output, thinking, total },
  costUsd: { input: inputCost, output: outputCost, total: totalCost },
  model: config.llm.model,
});
```

### 체크리스트
- [ ] 429만 지수 백오프 재시도, 400/403은 즉시 실패
- [ ] `AbortSignal.timeout()`으로 개별 요청 타임아웃
- [ ] markdown 코드블록 래핑 제거
- [ ] 모든 LLM 응답 필드에 타입 검증 + 기본값
- [ ] 매 호출마다 토큰 수 + 비용(USD) 로그
- [ ] thinking/reasoning 토큰 별도 추적

---

## Frontend Patterns (Vanilla JS SPA)

### ES Module 파일 분리
```
public/js/
├── app.js        # 진입점 (import 모든 모듈, 초기화)
├── state.js      # 공유 상태 (mutable 객체 export)
├── utils.js      # 순수 유틸리티 (escapeHtml, toLocalDateStr 등)
├── api.js        # fetchWithAuth, 토큰 갱신
├── analytics.js  # 이벤트 트래킹 (sendBeacon 배치)
├── auth.js       # 로그인/회원가입
├── [feature].js  # 기능별 모듈
```

**순환 의존성 방지**: dependency injection
```javascript
// feature.js — 상위 모듈 함수를 setup으로 주입
let deps = {};
export function setupFeature(d) { deps = d; }
// deps.showApp(), deps.showAuth() 등으로 호출

// app.js — 초기화 시 주입
import { setupFeature } from './feature.js';
setupFeature({ showApp, showAuth, migrateData });
```

### 공유 상태 (프레임워크 없이)
```javascript
// state.js
export const state = {
  currentUser: null,
  accessToken: null,
  refreshToken: null,
  allEntries: [],
  appInitialized: false,
};
// 모든 모듈이 같은 참조를 import하여 읽기/쓰기
```

### fetchWithAuth (인증 API 래퍼)
```javascript
export async function fetchWithAuth(url, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), TIMEOUT);

  try {
    const res = await fetch(url, {
      ...options,
      headers: { ...options.headers, 'Authorization': `Bearer ${state.accessToken}` },
      signal: controller.signal,
    });

    // 401: 토큰 갱신 후 1회 재시도
    if (res.status === 401 && state.refreshToken) {
      const refreshed = await tryRefreshToken();
      if (refreshed) return fetchWithAuth(url, { ...options, _retried: true });
    }
    return res;
  } finally { clearTimeout(timeout); }
}
```

### 타임존 처리 (핵심 규칙)
```javascript
// ✅ UTC → 로컬 날짜 변환
export function toLocalDateStr(dateOrStr) {
  const d = typeof dateOrStr === 'string' ? new Date(dateOrStr) : dateOrStr;
  return d.getFullYear() + '-' +
    String(d.getMonth() + 1).padStart(2, '0') + '-' +
    String(d.getDate()).padStart(2, '0');
}

// ❌ 절대 사용 금지
isoString.split('T')[0]           // UTC 날짜 반환 (로컬 아님)
new Date().toISOString().slice(0,10) // 같은 문제

// 서버 측: tz_offset 파라미터로 클라이언트 타임존 전달
params.set('tz_offset', new Date().getTimezoneOffset());
```

### 에러 핸들링 3계층
```javascript
// 1계층: API 에러 → userMessage 포함 throw
const err = new Error(data.error);
err.userMessage = data.error;
throw err;

// 2계층: 호출부 catch → graceful degradation
try { await loadData(); }
catch { showEmptyState(); }

// 3계층: 글로벌 핸들러 → 서버 전송 + 토스트
window.onerror = function(message, source, lineno, colno, error) {
  track('client_error', { message, source, lineno, colno, stack: error?.stack?.slice(0, 500) });
  showToast('오류가 발생했습니다.', 'error');
  return true;
};
```

### 이벤트 트래킹 (sendBeacon 배치)
```javascript
const queue = [];
export function track(event, props = {}) {
  queue.push({ event, ...props, timestamp: Date.now(), session_id: SESSION_ID });
  if (queue.length >= BATCH_SIZE) flush();
}

// 5초 주기 + 페이지 이탈 시 flush
setInterval(flush, 5000);
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'hidden') flush();
});

function flush() {
  if (queue.length === 0) return;
  const batch = queue.splice(0);
  navigator.sendBeacon('/api/analytics', JSON.stringify({ events: batch }));
}
```

### PWA / Service Worker
```javascript
// 요청별 캐시 전략
// 인증 API (/api/auth/*): network-only (캐시 금지)
// POST 요청: network-first + IndexedDB 오프라인 큐
// GET API: network-first (실패 시 캐시)
// 정적 자산: stale-while-revalidate

// 캐시 버전: 기능 변경마다 증가
const CACHE_VERSION = 'app-v1';

// 오프라인 큐: IndexedDB → 온라인 복귀 시 재전송
```

### 게스트 → 회원 전환
```javascript
// 게스트: localStorage에 최대 N건/M일 보관
// 넛지: 3회 사용 후 모달 표시
// 제한: N회 도달 시 회원가입 유도
// 전환: 회원가입 후 /api/migrate/from-guest로 일괄 마이그레이션
```

### CSS 구조 (4파일 분리)
```
css/
├── base.css        # :root 토큰(색상/그림자/반경/폰트), 리셋
├── layout.css      # 그리드, 탭, 사이드바
├── components.css  # UI 컴포넌트 + [data-theme="dark"] 토큰 오버라이드
└── landing.css     # 랜딩 페이지 전용
```

---

## Vercel Serverless Deployment

### 체크리스트
- [ ] `vercel.json`: 정적 파일은 `@vercel/static`, API는 `@vercel/node`
- [ ] 파일시스템 쓰기 금지 (`/tmp`는 임시 캐시용만)
- [ ] 로그: `console.log(JSON.stringify(...))` — Vercel이 수집
- [ ] ANSI 색상 코드 프로덕션에서 제거
- [ ] 환경변수 Vercel 대시보드에서 설정
- [ ] 프로덕션 환경 감지: `process.env.VERCEL || process.env.NODE_ENV === 'production'`

### vercel.json 템플릿
```json
{
  "version": 2,
  "builds": [
    { "src": "public/**", "use": "@vercel/static" },
    { "src": "server.js", "use": "@vercel/node" }
  ],
  "routes": [
    { "src": "/api/(.*)", "dest": "server.js" },
    { "src": "/sw.js", "dest": "public/sw.js" },
    { "src": "/(css|js|images)/(.*)", "dest": "public/$1/$2" },
    { "src": "/(.*)", "dest": "server.js" }
  ]
}
```

---

## Project Start Checklist

새 Express + Supabase + LLM 프로젝트 시작 시:

```
[ ] 1. config/ — 설정 외부화 (llm-config.js, db-config.js)
[ ] 2. lib/ — auth-middleware.js, validators.js
[ ] 3. server.js — 미들웨어 순서: helmet→cors→json→static→logging→routes→404→error
[ ] 4. Logger — 프로덕션=JSON, 로컬=컬러+파일
[ ] 5. requestId 미들웨어 + X-Request-Id 헤더
[ ] 6. routeDeps 의존성 주입으로 라우트 모듈 분리
[ ] 7. Rate limiter — 엔드포인트별 세분화
[ ] 8. RLS 정책 — SELECT에 soft delete 필터 포함
[ ] 9. 3가지 DB 클라이언트 (public/admin/user-scoped) 분리
[ ] 10. LLM — 재시도(429만) + 타임아웃 + 코드블록 파싱 + 비용 로깅
[ ] 11. 환경변수 검증 (서버 시작 시)
[ ] 12. Graceful shutdown + unhandled rejection 핸들러
[ ] 13. vercel.json 라우팅 설정
[ ] 14. 마이그레이션 순번 파일 (테이블→인덱스→RLS→트리거)
[ ] 15. 프론트엔드 — ES Module 분리 + state.js + fetchWithAuth
[ ] 16. 타임존 — toLocalDateStr() 유틸리티 (.split('T')[0] 금지)
[ ] 17. 에러 — 3계층 (API throw → catch → 글로벌 핸들러+서버 전송)
[ ] 18. 트래킹 — sendBeacon 배치 + 페이지 이탈 flush
[ ] 19. PWA — SW 캐시 전략 (인증=network-only, 정적=SWR)
[ ] 20. 문서 — README, CLAUDE.md, docs/API.md, docs/DEVLOG.md
```

---

## Key Lessons Learned

### 절대 하지 말 것
- `.split('T')[0]`으로 날짜 추출 → UTC 날짜가 됨 (로컬 아님)
- Supabase RLS에 `WITH CHECK (true)` INSERT 정책 → 누구나 삽입 가능
- Vercel에서 파일 로그 쓰기 → 서버 종료 시 소멸
- CSP에 `unsafe-inline` → XSS 취약점
- `service_role` 키를 클라이언트에 노출
- LLM 응답을 타입 검증 없이 사용
- DB의 UTC 시간값을 로컬 시간으로 "수정" → 이중 오프셋 발생
- 로그아웃 시 인증 토큰만 지우고 데이터 상태(entries, profile 등) 유지

### 반드시 할 것
- 환경변수에 기본값 제공 (`process.env.X || 'default'`)
- 보안 이벤트(로그인 실패 등) 별도 로깅
- 모든 사용자 입력을 escapeHtml() 처리
- DB 레벨에서 데이터 무결성 보장 (CHECK 제약조건)
- 커밋 전 서버 실행 확인
- 기능 추가 시 문서 동기화
- **로그아웃/계정 전환 시 모든 유저 데이터 상태 초기화** (token + profile + cached data + UI state)
- **Supabase Auth 리다이렉트 URL 명시 설정** (signUp → emailRedirectTo, OAuth → redirectTo)
- **service_role 의존 기능은 키 부재 시 startup 경고** (silent fail 방지)
- **배포 환경변수 체크리스트 유지** (SUPABASE_URL, ANON_KEY, SERVICE_ROLE_KEY, SITE_URL, API keys)
