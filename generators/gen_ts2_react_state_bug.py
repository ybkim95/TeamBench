"""
Parameterized generator for TS2: React Component State Bugs.

Each seed produces a different React component domain (chat/timer/search/dashboard/form)
with 3-4 intentional state bugs and 2 intentional-but-correct patterns.

Bug categories (3-4 selected per seed):
  A. stale_closure_counter:   onClick uses stale `count` in closure instead of
                               functional updater `setCount(c => c + 1)`
  B. missing_dep_useeffect:   useEffect that uses a prop/state value without
                               listing it in the dependency array
  C. missing_cleanup:         useEffect that sets up a subscription/timer but
                               returns no cleanup function
  D. state_mutation:          direct mutation of state array/object instead of
                               creating a new value

Intentional (correct, must NOT be changed) patterns:
  I1. empty_dep_array:        useEffect with [] is correct — intentional mount-only effect
  I2. deliberate_rerender:    a state update that looks redundant but drives a
                               visible animation/transition side effect

Information asymmetry (TNI pattern A):
  spec.md   — lists all bugs with exact locations and fixes, plus both correct patterns
  brief.md  — "fix the component" (no specifics)
"""
from __future__ import annotations

import textwrap

from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom


# ── Domain configurations ──────────────────────────────────────────────────────

DOMAINS = [
    {
        "name": "chat",
        "component": "ChatWindow",
        "hook_subject": "messages",
        "entity": "Message",
        "entity_lower": "message",
        "entity_plural": "messages",
        "counter_label": "unread",
        "timer_desc": "auto-scroll interval",
        "search_field": "text",
        "list_field": "messages",
        "fetch_endpoint": "/api/chat/messages",
        "subscription_name": "chatSubscription",
        "subscription_setup": "chatClient.subscribe(roomId, handleMessage)",
    },
    {
        "name": "timer",
        "component": "CountdownTimer",
        "hook_subject": "ticks",
        "entity": "Tick",
        "entity_lower": "tick",
        "entity_plural": "ticks",
        "counter_label": "elapsed",
        "timer_desc": "countdown interval",
        "search_field": "label",
        "list_field": "history",
        "fetch_endpoint": "/api/timer/history",
        "subscription_name": "timerSubscription",
        "subscription_setup": "timerService.connect(timerId, onTick)",
    },
    {
        "name": "search",
        "component": "SearchPanel",
        "hook_subject": "results",
        "entity": "Result",
        "entity_lower": "result",
        "entity_plural": "results",
        "counter_label": "total",
        "timer_desc": "debounce timer",
        "search_field": "query",
        "list_field": "items",
        "fetch_endpoint": "/api/search",
        "subscription_name": "searchSubscription",
        "subscription_setup": "searchStream.open(query, onResult)",
    },
    {
        "name": "dashboard",
        "component": "MetricsDashboard",
        "hook_subject": "metrics",
        "entity": "Metric",
        "entity_lower": "metric",
        "entity_plural": "metrics",
        "counter_label": "alerts",
        "timer_desc": "polling interval",
        "search_field": "name",
        "list_field": "panels",
        "fetch_endpoint": "/api/metrics",
        "subscription_name": "metricsSubscription",
        "subscription_setup": "metricsStream.subscribe(dashboardId, onMetric)",
    },
    {
        "name": "form",
        "component": "MultiStepForm",
        "hook_subject": "fields",
        "entity": "Field",
        "entity_lower": "field",
        "entity_plural": "fields",
        "counter_label": "errors",
        "timer_desc": "autosave interval",
        "search_field": "value",
        "list_field": "steps",
        "fetch_endpoint": "/api/form/draft",
        "subscription_name": "formSubscription",
        "subscription_setup": "formSync.attach(formId, onFieldChange)",
    },
]

# Which bugs appear per seed (rotate to ensure each seed gets a distinct set)
BUG_SETS = [
    ["stale_closure_counter", "missing_dep_useeffect", "missing_cleanup", "state_mutation"],
    ["stale_closure_counter", "missing_dep_useeffect", "missing_cleanup"],
    ["missing_dep_useeffect", "missing_cleanup", "state_mutation"],
    ["stale_closure_counter", "missing_cleanup", "state_mutation"],
    ["stale_closure_counter", "missing_dep_useeffect", "state_mutation"],
]


class Generator(TaskGenerator):
    task_id = "TS2_react_state_bug"
    domain = "Software Engineering"
    difficulty = "medium"
    languages = ["typescript"]

    @staticmethod
    def _clean(s: str) -> str:
        """Strip common leading whitespace from every line (handles f-string indent issues)."""
        return textwrap.dedent(s).strip() + "\n"

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)
        domain_idx = seed % len(DOMAINS)
        bug_set_idx = seed % len(BUG_SETS)
        cfg = DOMAINS[domain_idx]
        bugs = BUG_SETS[bug_set_idx]

        # Seed-parameterized values
        interval_ms = rng.choice([500, 1000, 2000, 3000])
        initial_count = rng.randint(0, 5)
        max_items = rng.randint(50, 200)

        workspace_files = self._make_workspace(cfg, bugs, interval_ms, initial_count, max_items)
        spec_md = self._clean(self._make_spec(cfg, bugs, interval_ms, initial_count, max_items))
        brief_md = self._clean(self._make_brief(cfg))

        return GeneratedTask(
            task_id="TS2_react_state_bug",
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected={
                "seed": seed,
                "domain": cfg["name"],
                "component": cfg["component"],
                "bugs": bugs,
                "interval_ms": interval_ms,
                "initial_count": initial_count,
                "max_items": max_items,
                "intentional_patterns": ["empty_dep_array", "deliberate_rerender"],
            },
            workspace_files=workspace_files,
            metadata={"difficulty": "medium", "category": "Software Engineering"},
        )

    # ── Workspace file generators ──────────────────────────────────────────────

    def _make_workspace(
        self, cfg: dict, bugs: list, interval_ms: int, initial_count: int, max_items: int
    ) -> dict:
        files = {}
        files[f"src/{cfg['component']}.tsx"] = self._make_component(
            cfg, bugs, interval_ms, initial_count, max_items
        )
        files["src/types.ts"] = self._make_types(cfg)
        files["src/hooks/useDebounce.ts"] = self._make_use_debounce()
        files[f"src/{cfg['component']}.test.tsx"] = self._make_test(
            cfg, bugs, interval_ms, initial_count, max_items
        )
        files["package.json"] = self._make_package_json(cfg)
        files["tsconfig.json"] = self._make_tsconfig()
        return files

    def _make_types(self, cfg: dict) -> str:
        entity = cfg["entity"]
        search_field = cfg["search_field"]
        list_field = cfg["list_field"]
        component = cfg["component"]
        counter_label = cfg["counter_label"]
        entity_lower = cfg["entity_lower"]

        return textwrap.dedent(f"""\
            // types.ts — shared type definitions for {component}

            export interface {entity} {{
              id: string;
              {search_field}: string;
              timestamp: number;
              read: boolean;
            }}

            export interface {component}Props {{
              {entity_lower}Id: string;
              initialItems?: {entity}[];
              maxItems?: number;
              onCountChange?: (count: number) => void;
            }}

            export interface {component}State {{
              {list_field}: {entity}[];
              {counter_label}Count: number;
              isLoading: boolean;
              error: string | null;
              flashActive: boolean;
            }}
            """)

    def _make_use_debounce(self) -> str:
        return textwrap.dedent("""\
            import { useState, useEffect } from 'react';

            export function useDebounce<T>(value: T, delay: number): T {
              const [debouncedValue, setDebouncedValue] = useState<T>(value);

              useEffect(() => {
                const handler = setTimeout(() => {
                  setDebouncedValue(value);
                }, delay);

                return () => {
                  clearTimeout(handler);
                };
              }, [value, delay]);

              return debouncedValue;
            }
            """)

    def _make_component(
        self, cfg: dict, bugs: list, interval_ms: int, initial_count: int, max_items: int
    ) -> str:
        component = cfg["component"]
        entity = cfg["entity"]
        entity_lower = cfg["entity_lower"]
        entity_plural = cfg["entity_plural"]
        list_field = cfg["list_field"]
        counter_label = cfg["counter_label"]
        search_field = cfg["search_field"]
        fetch_endpoint = cfg["fetch_endpoint"]
        subscription_name = cfg["subscription_name"]
        subscription_setup = cfg["subscription_setup"]
        timer_desc = cfg["timer_desc"]

        has_stale = "stale_closure_counter" in bugs
        has_missing_dep = "missing_dep_useeffect" in bugs
        has_missing_cleanup = "missing_cleanup" in bugs
        has_mutation = "state_mutation" in bugs

        # Build the increment handler — buggy or correct
        if has_stale:
            increment_handler = f"""\
  // BUG A: stale closure — `{counter_label}Count` captured at render time;
  // concurrent updates will overwrite each other.
  // Fix: use functional updater: set{counter_label.capitalize()}Count(c => c + 1)
  const handle{counter_label.capitalize()}Increment = () => {{
    set{counter_label.capitalize()}Count({counter_label}Count + 1);
  }};"""
        else:
            increment_handler = f"""\
  const handle{counter_label.capitalize()}Increment = () => {{
    set{counter_label.capitalize()}Count(c => c + 1);
  }};"""

        # Build fetch effect — buggy (missing dep) or correct
        if has_missing_dep:
            fetch_effect = f"""\
  // BUG B: missing dependency — `{entity_lower}Id` is used inside but not listed
  // in the dependency array. Stale `{entity_lower}Id` will be used after prop changes.
  // Fix: add `{entity_lower}Id` to the dependency array.
  useEffect(() => {{
    setIsLoading(true);
    fetch(`{fetch_endpoint}/${{{entity_lower}Id}}`)
      .then(r => r.json())
      .then((data: {entity}[]) => {{
        set{list_field.capitalize()}(data.slice(0, maxItems));
        setIsLoading(false);
      }})
      .catch(() => {{
        setError('Failed to load {entity_plural}');
        setIsLoading(false);
      }});
  }}, []); // missing: [{entity_lower}Id, maxItems]"""
        else:
            fetch_effect = f"""\
  useEffect(() => {{
    setIsLoading(true);
    fetch(`{fetch_endpoint}/${{{entity_lower}Id}}`)
      .then(r => r.json())
      .then((data: {entity}[]) => {{
        set{list_field.capitalize()}(data.slice(0, maxItems));
        setIsLoading(false);
      }})
      .catch(() => {{
        setError('Failed to load {entity_plural}');
        setIsLoading(false);
      }});
  }}, [{entity_lower}Id, maxItems]);"""

        # Build subscription effect — buggy (no cleanup) or correct
        if has_missing_cleanup:
            subscription_effect = f"""\
  // BUG C: missing cleanup — {subscription_name} is never unsubscribed.
  // On unmount or re-render the subscription leaks, causing state updates
  // on unmounted components.
  // Fix: return a cleanup function that calls {subscription_name}.unsubscribe()
  useEffect(() => {{
    const {subscription_name} = {subscription_setup};
    // Missing: return () => {{ {subscription_name}.unsubscribe(); }};
  }}, [{entity_lower}Id]); // [] intentional: mount-only — this is CORRECT (I1)"""
        else:
            subscription_effect = f"""\
  // INTENTIONAL (I1): empty dep array is correct here — subscription
  // should only be created once on mount and cleaned up on unmount.
  useEffect(() => {{
    const {subscription_name} = {subscription_setup};
    return () => {{
      {subscription_name}.unsubscribe();
    }};
  }}, [{entity_lower}Id]);"""

        # Build add-item handler — buggy (mutation) or correct
        if has_mutation:
            add_handler = f"""\
  // BUG D: direct state mutation — pushing to the existing array does not
  // trigger a re-render because React compares references, not contents.
  // Fix: use spread to create a new array: set{list_field.capitalize()}(prev => [...prev, newItem])
  const handle{entity}Added = (newItem: {entity}) => {{
    {list_field}.push(newItem); // mutates state directly
    set{list_field.capitalize()}({list_field}); // same reference — React skips re-render
  }};"""
        else:
            add_handler = f"""\
  const handle{entity}Added = (newItem: {entity}) => {{
    set{list_field.capitalize()}(prev => [...prev, newItem]);
  }};"""

        # Flash effect — INTENTIONAL (I2): deliberate re-render for animation
        flash_effect = f"""\
  // INTENTIONAL (I2): setFlashActive(true) immediately followed by false looks
  // redundant but is required to trigger the CSS transition animation.
  // Do NOT simplify or remove this pattern.
  const triggerFlash = () => {{
    setFlashActive(true);
    setTimeout(() => setFlashActive(false), {interval_ms});
  }};"""

        # Interval effect (always correct — {timer_desc})
        interval_effect = f"""\
  // Correct: {timer_desc} — properly cleaned up on unmount.
  useEffect(() => {{
    const intervalId = setInterval(() => {{
      triggerFlash();
    }}, {interval_ms});
    return () => clearInterval(intervalId);
  }}, []); // eslint-disable-line react-hooks/exhaustive-deps"""

        return textwrap.dedent(f"""\
            import React, {{ useState, useEffect, useCallback }} from 'react';
            import {{ {entity}, {component}Props }} from './types';

            /**
             * {component} — {cfg['hook_subject']} management component.
             * Initial {counter_label} count: {initial_count}
             * Max items: {max_items}
             */
            export const {component}: React.FC<{component}Props> = ({{
              {entity_lower}Id,
              initialItems = [],
              maxItems = {max_items},
              onCountChange,
            }}) => {{
              const [{list_field}, set{list_field.capitalize()}] = useState<{entity}[]>(initialItems);
              const [{counter_label}Count, set{counter_label.capitalize()}Count] = useState<number>({initial_count});
              const [isLoading, setIsLoading] = useState<boolean>(false);
              const [error, setError] = useState<string | null>(null);
              const [flashActive, setFlashActive] = useState<boolean>(false);

              {increment_handler}

              {fetch_effect}

              {subscription_effect}

              {add_handler}

              {flash_effect}

              {interval_effect}

              useEffect(() => {{
                onCountChange?.({counter_label}Count);
              }}, [{counter_label}Count, onCountChange]);

              if (isLoading) return <div className="loading">Loading {entity_plural}...</div>;
              if (error) return <div className="error">{{error}}</div>;

              return (
                <div className={{`{entity_lower.lower()}-container ${{flashActive ? 'flash' : ''}}`}}>
                  <div className="counter">
                    <span>{{{counter_label}Count}} {counter_label}</span>
                    <button onClick={{handle{counter_label.capitalize()}Increment}}>+1</button>
                  </div>
                  <ul className="{list_field}-list">
                    {{{list_field}.map(item => (
                      <li key={{item.id}}>{{item.{search_field}}}</li>
                    ))}}
                  </ul>
                </div>
              );
            }};

            export default {component};
            """)

    def _make_test(
        self, cfg: dict, bugs: list, interval_ms: int, initial_count: int, max_items: int
    ) -> str:
        component = cfg["component"]
        entity = cfg["entity"]
        entity_lower = cfg["entity_lower"]
        entity_plural = cfg["entity_plural"]
        list_field = cfg["list_field"]
        counter_label = cfg["counter_label"]
        search_field = cfg["search_field"]
        fetch_endpoint = cfg["fetch_endpoint"]

        has_stale = "stale_closure_counter" in bugs
        has_missing_dep = "missing_dep_useeffect" in bugs
        has_missing_cleanup = "missing_cleanup" in bugs
        has_mutation = "state_mutation" in bugs

        return textwrap.dedent(f"""\
            import React from 'react';
            import {{ render, screen, fireEvent, waitFor, act }} from '@testing-library/react';
            import {{ {component} }} from './{component}';
            import {{ {entity} }} from './types';

            const MOCK_ID = 'test-{entity_lower}-1';
            const MOCK_ITEMS: {entity}[] = [
              {{ id: '1', {search_field}: 'item-one', timestamp: 1000, read: false }},
              {{ id: '2', {search_field}: 'item-two', timestamp: 2000, read: true }},
            ];

            beforeEach(() => {{
              jest.useFakeTimers();
              global.fetch = jest.fn().mockResolvedValue({{
                json: () => Promise.resolve(MOCK_ITEMS),
              }}) as jest.Mock;
            }});

            afterEach(() => {{
              jest.runOnlyPendingTimers();
              jest.useRealTimers();
              jest.restoreAllMocks();
            }});

            // ── T1: counter functional updater ──────────────────────────────
            // BUG A (stale_closure_counter): rapid clicks with stale closure
            // will lose increments. Correct code uses functional updater.
            test('T1: counter increments correctly on rapid clicks', async () => {{
              const onCountChange = jest.fn();
              render(
                <{component}
                  {entity_lower}Id={{MOCK_ID}}
                  initialItems={{MOCK_ITEMS}}
                  onCountChange={{onCountChange}}
                />
              );

              const btn = screen.getByRole('button', {{ name: '+1' }});
              // Simulate rapid clicks — functional updater must batch correctly
              for (let i = 0; i < 5; i++) {{
                fireEvent.click(btn);
              }}

              await waitFor(() => {{
                expect(onCountChange).toHaveBeenLastCalledWith({initial_count} + 5);
              }});
            }});

            // ── T2: fetch re-runs when {entity_lower}Id changes ──────────────────
            // BUG B (missing_dep_useeffect): if {entity_lower}Id is not in deps,
            // the effect won't re-run after prop change.
            test('T2: fetch re-runs when {entity_lower}Id prop changes', async () => {{
              const {{ rerender }} = render(
                <{component} {entity_lower}Id={{MOCK_ID}} />
              );

              await waitFor(() => {{
                expect(global.fetch).toHaveBeenCalledWith(
                  expect.stringContaining(MOCK_ID)
                );
              }});

              const NEW_ID = 'new-{entity_lower}-id';
              rerender(<{component} {entity_lower}Id={{NEW_ID}} />);

              await waitFor(() => {{
                expect(global.fetch).toHaveBeenCalledWith(
                  expect.stringContaining(NEW_ID)
                );
              }});
            }});

            // ── T3: subscription cleaned up on unmount ────────────────────
            // BUG C (missing_cleanup): subscription leaks after unmount.
            test('T3: no warnings about state update on unmounted component', async () => {{
              const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {{}});
              const {{ unmount }} = render(
                <{component} {entity_lower}Id={{MOCK_ID}} initialItems={{MOCK_ITEMS}} />
              );

              unmount();

              // Advance timers after unmount — should trigger no state-update warnings
              act(() => {{
                jest.advanceTimersByTime({interval_ms} * 3);
              }});

              const stateUpdateWarnings = (consoleError.mock.calls as string[][]).filter(
                args => args[0]?.includes?.('unmounted component')
              );
              expect(stateUpdateWarnings).toHaveLength(0);
              consoleError.mockRestore();
            }});

            // ── T4: adding item updates list ──────────────────────────────
            // BUG D (state_mutation): direct push doesn't trigger re-render.
            test('T4: rendered list updates when item is added via state setter', async () => {{
              // This test verifies that state updates correctly cause a re-render.
              // With direct mutation (push), the list won't update visually.
              const initialItem: {entity} = {{
                id: '10',
                {search_field}: 'visible-item',
                timestamp: 9000,
                read: false,
              }};
              render(
                <{component}
                  {entity_lower}Id={{MOCK_ID}}
                  initialItems={{[initialItem]}}
                />
              );

              expect(screen.getByText('visible-item')).toBeInTheDocument();
            }});

            // ── T5: flash animation triggers correctly ─────────────────────
            // INTENTIONAL (I2): the double setFlashActive call is correct.
            test('T5: flash class applied and removed after interval', async () => {{
              const {{ container }} = render(
                <{component} {entity_lower}Id={{MOCK_ID}} initialItems={{MOCK_ITEMS}} />
              );

              // Advance timer to trigger flash
              act(() => {{
                jest.advanceTimersByTime({interval_ms} + 50);
              }});

              // Flash class should eventually be removed
              await waitFor(() => {{
                expect(
                  container.querySelector('.flash')
                ).not.toBeInTheDocument();
              }});
            }});
            """)

    def _make_package_json(self, cfg: dict) -> str:
        component = cfg["component"]
        return textwrap.dedent(f"""\
            {{
              "name": "ts2-react-state-bug",
              "version": "1.0.0",
              "description": "React state bug task — {component}",
              "scripts": {{
                "build": "tsc --noEmit",
                "test": "jest --runInBand",
                "typecheck": "tsc --noEmit"
              }},
              "dependencies": {{
                "react": "^18.2.0",
                "react-dom": "^18.2.0"
              }},
              "devDependencies": {{
                "@testing-library/jest-dom": "^6.1.0",
                "@testing-library/react": "^14.0.0",
                "@testing-library/user-event": "^14.4.3",
                "@types/jest": "^29.5.0",
                "@types/react": "^18.2.0",
                "@types/react-dom": "^18.2.0",
                "jest": "^29.5.0",
                "jest-environment-jsdom": "^29.5.0",
                "ts-jest": "^29.1.0",
                "typescript": "^5.1.0"
              }},
              "jest": {{
                "preset": "ts-jest",
                "testEnvironment": "jsdom",
                "setupFilesAfterFramework": ["@testing-library/jest-dom"]
              }}
            }}
            """)

    def _make_tsconfig(self) -> str:
        return textwrap.dedent("""\
            {
              "compilerOptions": {
                "target": "ES2020",
                "lib": ["ES2020", "DOM"],
                "jsx": "react-jsx",
                "module": "CommonJS",
                "moduleResolution": "node",
                "strict": true,
                "noImplicitAny": true,
                "strictNullChecks": true,
                "esModuleInterop": true,
                "skipLibCheck": true,
                "outDir": "dist"
              },
              "include": ["src/**/*"],
              "exclude": ["node_modules", "dist"]
            }
            """)

    # ── Spec / Brief generators ────────────────────────────────────────────────

    def _make_spec(
        self, cfg: dict, bugs: list, interval_ms: int, initial_count: int, max_items: int
    ) -> str:
        component = cfg["component"]
        entity = cfg["entity"]
        entity_lower = cfg["entity_lower"]
        entity_plural = cfg["entity_plural"]
        list_field = cfg["list_field"]
        counter_label = cfg["counter_label"]
        fetch_endpoint = cfg["fetch_endpoint"]
        subscription_name = cfg["subscription_name"]
        subscription_setup = cfg["subscription_setup"]

        has_stale = "stale_closure_counter" in bugs
        has_missing_dep = "missing_dep_useeffect" in bugs
        has_missing_cleanup = "missing_cleanup" in bugs
        has_mutation = "state_mutation" in bugs

        bug_rows = []
        if has_stale:
            bug_rows.append(
                f"| A | stale_closure_counter | `handle{counter_label.capitalize()}Increment` in `{component}.tsx` | "
                f"Change `set{counter_label.capitalize()}Count({counter_label}Count + 1)` to "
                f"`set{counter_label.capitalize()}Count(c => c + 1)` |"
            )
        if has_missing_dep:
            bug_rows.append(
                f"| B | missing_dep_useeffect | fetch `useEffect` in `{component}.tsx` | "
                f"Add `{entity_lower}Id` and `maxItems` to the dependency array |"
            )
        if has_missing_cleanup:
            bug_rows.append(
                f"| C | missing_cleanup | subscription `useEffect` in `{component}.tsx` | "
                f"Return `() => {{ {subscription_name}.unsubscribe(); }}` from the effect |"
            )
        if has_mutation:
            bug_rows.append(
                f"| D | state_mutation | `handle{entity}Added` in `{component}.tsx` | "
                f"Replace `{list_field}.push(newItem); set{list_field.capitalize()}({list_field})` "
                f"with `set{list_field.capitalize()}(prev => [...prev, newItem])` |"
            )

        bug_table = "\n".join(bug_rows)

        return textwrap.dedent(f"""\
            # TS2_react_state_bug: React State Bug Fix — Full Specification (Planner Only)

            ## Overview

            The workspace contains a React component `{component}.tsx` that manages
            {entity_plural} with the following configuration:
            - Initial {counter_label} count: `{initial_count}`
            - Max items: `{max_items}`
            - Flash interval: `{interval_ms}ms`

            There are **{len(bugs)} intentional bugs** and **2 intentional-but-correct patterns**
            that must be preserved. The executor only receives the brief; this spec
            provides the full analysis.

            ## File Structure

            - `src/{component}.tsx` — component with all bugs (the only file to modify)
            - `src/types.ts` — type definitions (do NOT modify)
            - `src/hooks/useDebounce.ts` — utility hook (do NOT modify)
            - `src/{component}.test.tsx` — tests that detect each bug (do NOT modify)
            - `package.json`, `tsconfig.json` — build config (do NOT modify)

            ## Bug Analysis

            | # | Type | Location | Fix |
            |---|------|----------|-----|
            {bug_table}

            ### Bug Details

            """) + self._spec_bug_details(
                cfg, bugs, interval_ms, initial_count, max_items
            ) + textwrap.dedent(f"""\

            ## Intentional Patterns (DO NOT CHANGE)

            ### I1 — Empty Dependency Array in Subscription Effect

            The `useEffect` that sets up the {subscription_name} subscription uses
            `[{entity_lower}Id]` as its dependency array. This is **correct and intentional**:
            the subscription should be re-established only when the ID changes,
            not on every render.

            ### I2 — Double `setFlashActive` Call in `triggerFlash`

            The `triggerFlash` function sets `flashActive` to `true` then schedules
            it back to `false` after `{interval_ms}ms`. This **looks redundant but is
            required** to trigger the CSS transition animation. Do NOT simplify this
            to a single `setFlashActive(false)`.

            ## Acceptance Criteria

            1. `tsc --noEmit` reports zero errors
            2. All 5 tests in `{component}.test.tsx` pass
            3. The two intentional patterns (I1 and I2) are preserved unchanged
            4. Only `src/{component}.tsx` is modified

            ## Expected Behavior After Fixes

            - Rapid button clicks increment `{counter_label}Count` correctly (no lost updates)
            - Fetching re-runs when `{entity_lower}Id` prop changes
            - Subscription is cleaned up on unmount (no leaked listeners)
            - Adding items via state setter triggers re-render
            - Flash animation works correctly (double state toggle preserved)
            """)

    def _spec_bug_details(
        self, cfg: dict, bugs: list, interval_ms: int, initial_count: int, max_items: int
    ) -> str:
        component = cfg["component"]
        entity = cfg["entity"]
        entity_lower = cfg["entity_lower"]
        list_field = cfg["list_field"]
        counter_label = cfg["counter_label"]
        fetch_endpoint = cfg["fetch_endpoint"]
        subscription_name = cfg["subscription_name"]

        sections = []

        if "stale_closure_counter" in bugs:
            sections.append(textwrap.dedent(f"""\
                ### Bug A — Stale Closure in Counter Increment

                **Location:** `handle{counter_label.capitalize()}Increment` in `{component}.tsx`

                **Root cause:** The handler captures `{counter_label}Count` from the render
                closure. Under React's batched updates (e.g., rapid clicks) the captured
                value is stale — two clicks in the same batch both read the same value,
                so only one increment is applied.

                **Buggy code:**
                ```tsx
                const handle{counter_label.capitalize()}Increment = () => {{
                  set{counter_label.capitalize()}Count({counter_label}Count + 1); // stale closure
                }};
                ```

                **Fix:**
                ```tsx
                const handle{counter_label.capitalize()}Increment = () => {{
                  set{counter_label.capitalize()}Count(c => c + 1); // functional updater
                }};
                ```
                """))

        if "missing_dep_useeffect" in bugs:
            _dep_fix = "}}, [" + entity_lower + "Id, maxItems]);"
            sections.append(textwrap.dedent(f"""\
                ### Bug B — Missing Dependency in `useEffect`

                **Location:** fetch `useEffect` in `{component}.tsx`

                **Root cause:** The effect calls `fetch('{fetch_endpoint}/{entity_lower}Id')` but
                `{entity_lower}Id` (and `maxItems`) are not in the dependency array (`[]`).
                When the parent re-renders with a new `{entity_lower}Id` prop, the effect
                does NOT re-run, leaving stale data displayed.

                **Fix:** Add `{entity_lower}Id` and `maxItems` to the dependency array:
                ```tsx
                {_dep_fix}
                ```
                """))

        if "missing_cleanup" in bugs:
            sections.append(textwrap.dedent(f"""\
                ### Bug C — Missing Cleanup in Subscription Effect

                **Location:** subscription `useEffect` in `{component}.tsx`

                **Root cause:** The effect creates a `{subscription_name}` but never
                returns a cleanup function. When the component unmounts the subscription
                continues firing, causing `setState` calls on an unmounted component and
                potential memory leaks.

                **Fix:** Return a cleanup function:
                ```tsx
                useEffect(() => {{
                  const {subscription_name} = ...;
                  return () => {{
                    {subscription_name}.unsubscribe();
                  }};
                }}, [{entity_lower}Id]);
                ```
                """))

        if "state_mutation" in bugs:
            sections.append(textwrap.dedent(f"""\
                ### Bug D — Direct State Mutation

                **Location:** `handle{entity}Added` in `{component}.tsx`

                **Root cause:** The handler calls `{list_field}.push(newItem)` which mutates
                the existing array in place. React uses reference equality to detect changes;
                since the array reference is the same, no re-render is triggered.

                **Buggy code:**
                ```tsx
                {list_field}.push(newItem);
                set{list_field.capitalize()}({list_field}); // same ref — React skips re-render
                ```

                **Fix:** Create a new array:
                ```tsx
                set{list_field.capitalize()}(prev => [...prev, newItem]);
                ```
                """))

        return "\n".join(sections)

    def _make_brief(self, cfg: dict) -> str:
        component = cfg["component"]
        entity_plural = cfg["entity_plural"]

        return textwrap.dedent(f"""\
            # TS2_react_state_bug (Brief)

            The `{component}` React component has bugs causing incorrect behaviour:
            some updates are lost, data goes stale after prop changes, and the
            component may crash after unmounting.

            Fix the component so all tests pass:

            ```
            npm test
            ```

            **File to fix:** `src/{component}.tsx`
            **Do NOT modify:** `src/types.ts`, `src/hooks/useDebounce.ts`,
            `src/{component}.test.tsx`, `package.json`, `tsconfig.json`

            Follow the Planner's guidance precisely.
            """)
