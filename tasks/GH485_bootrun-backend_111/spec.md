# GH485_bootrun-backend_111: [FIX] completion_rate 100% 초과 방지 및 진행률 계산 개선 — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/I5-Team/bootrun-backend/issues/105
- Repo: https://github.com/I5-Team/bootrun-backend

## Issue Description

<img width="1277" height="257" alt="Image" src="https://github.com/user-attachments/assets/40691af5-f6b9-4c62-a226-71730d82e1bb" />

<img width="1277" height="257" alt="Image" src="https://github.com/user-attachments/assets/d6b8535a-71cd-4edf-8296-5bfb4a9dbb8f" />

상단 이미지 로그 중에서 completion_rate 확인 요청

## 어떤 이슈 인가요?
> 버그: 강의 진행률 API가 100% 초과 값을 반환

## 문제 설명
강의 진행률 API(`PATCH /api/enrollments/lectures/{id}/progress`)가 `completion_rate` 값을 100% 초과하는 값으로 반환하고 있습니다.

### 테스트 환경
1. 테스트 계정([email redacted] / Test1234!@)
2. http://localhost:5174/bootrun-frontend/lectures/1/room 접속
3. 두더지 나와유 > "three.js 기본기와 3D 두더지 게임 설계"> " Scene, Camera, Renderer 개념 잡기" 등 재생하면 현재 일부 강의에서 completion_rate에서 100을 초과하는 값을 반환

### 실제 서버 응답 (스크린샷 참조)
```json
{
  "completion_rate": 203.93700787401573, 
duration_seconds: 254,
is_completed : true,
last_position: 518,
last_watched_at: "2025-11-30T03:26:53.538594",
lecture_id: 43,
lecture_title: " Scene, Camera, Renderer 개념 잡기",
watched_seconds: 518
}
```

개인적인 생각으로는 영상을 앞뒤로 이동하면서 시청하면서 시청시간이 누적된 것 같기도 합니다...! 확인 부탁드립니다!

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

[user] [user] [user] 
강의실 쪽 작업하다가 확인이 필요한 사항을 발견하여, 백엔드 issue에 공유 드립니다!

## PR Review Comments

**[user]** on `alembic/versions/a3a28d52a24f_add_unique_watched_seconds_to_progress.py`:

**Data Migration Issue**: The migration sets `unique_watched_seconds = watched_seconds` for existing records, but this is incorrect. Based on the PR's logic, `unique_watched_seconds` should be set to `min(watched_seconds, lecture.duration_seconds)` or ideally to `last_position` (which represents the furthest point reached).

Setting it to `watched_seconds` means existing users who have rewatched portions of videos will have inflated `unique_watched_seconds` values, potentially causing completion rates to still exceed 100% until they next update their progress.

Consider updating the migration to:
```python
UPDATE progresses p
SET unique_watched_seconds = LEAST(p.last_position, 
    (SELECT l.duration_seconds FROM lectures l WHERE l.id = p.lecture_id))
```
```suggestion
    # Update existing records: set unique_watched_seconds to min(last_position, lecture.duration_seconds)
    op.execute("""
        UPDATE progresses p
        SET unique_watched_seconds = LEAST(
            p.last_position,
            (SELECT l.duration_seconds FROM lectures l WHERE l.id = p.lecture_id)
        )
```

**[user]** on `app/services/enrollment_service.py`:

**Misleading Documentation**: The comment states "last_position을 기준으로 유니크 시청 시간 계산" (Calculate unique watch time based on last_position), but the implementation `unique_watched_seconds = last_position` is problematic because:

1. This is not really calculating "unique" watched time - it's just copying `last_position`
2. The comment suggests a calculation is happening, but it's just an assignment
3. This will cause `unique_watched_seconds` to decrease when users rewind

If the intended behavior is to track the furthest position reached, the comment should be updated to reflect that, and the field should perhaps be renamed to something like `max_position_reached` for clarity. If true unique watched time tracking is needed, a different algorithm is required.

**[user]** on `app/services/enrollment_service.py`:

**Misleading Documentation**: Same issue as in `create_progress`. The comment "last_position을 기준으로 유니크 시청 시간 계산" is misleading because the implementation doesn't truly calculate unique watched time and will decrease the value when users rewind.
```suggestion
        # last_position 값을 unique_watched_seconds로 사용
```

**[user]** on `app/services/enrollment_service.py`:

[nitpick] **Potential Edge Case**: When `lecture.duration_seconds` is 0, `last_position` is set to `data.last_position` without any constraint. While this might be intentional (to preserve the original value for zero-duration lectures), it could lead to inconsistent data if the frontend sends incorrect values.

Consider whether zero-duration lectures should be handled specially, or if `last_position` should always be clamped to 0 when duration is 0:
```python
last_position = min(data.last_position, lecture.duration_seconds) if lecture.duration_seconds > 0 else 0
```
```suggestion
        last_position = min(data.last_position, lecture.duration_seconds) if lecture.duration_seconds > 0 else 0
```

**[user]** on `app/services/enrollment_service.py`:

[nitpick] **Potential Edge Case**: Same as in `create_progress` - when `progress.lecture.duration_seconds` is 0, `last_position` remains unconstrained. Consider clamping to 0 for consistency.
```suggestion
        last_position = min(data.last_position, progress.lecture.duration_seconds) if progress.lecture.duration_seconds > 0 else 0
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
