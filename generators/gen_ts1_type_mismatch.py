"""
Parameterized generator for TS1: TypeScript API Type Mismatch.

Each seed produces a different API domain (users/products/orders/invoices/events)
with 4-6 intentional type mismatches between shared types (types.ts) and the
handler/service implementations.

Mismatch categories (4-6 selected per seed):
  A. wrong_field_name:       handler destructures `titleValue` but types.ts says `title`
  B. wrong_primitive_type:   service annotates field as `string` but types.ts says `number`
  C. optional_as_required:   handler accesses `result.email.toString()` without null check
  D. missing_required_field: service list fn omits a required field from returned objects
  E. wrong_return_type:      helper annotated as `(): string` but actually returns number
  F. date_as_string:         service assigns `new Date().toISOString()` (string) for Date field

Information asymmetry:
  - spec.md lists every mismatch with file location and exact fix
  - brief.md only says "there are type errors; fix them so tsc passes"
"""
from __future__ import annotations

from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom


# ── Domain configurations ─────────────────────────────────────────────────────

DOMAINS = [
    {
        "name": "users",
        "entity": "User",
        "entity_lower": "user",
        "entity_plural": "Users",
        "route_prefix": "/users",
        "fields": [
            ("id", "number"),
            ("username", "string"),
            ("email", "string"),
            ("age", "number"),
            ("active", "boolean"),
            ("createdAt", "Date"),
        ],
        "optional_fields": ["email", "age"],
        "sample_values": {
            "id": "1",
            "username": '"alice"',
            "email": '"alice@example.com"',
            "age": "30",
            "active": "true",
            "createdAt": "new Date()",
        },
    },
    {
        "name": "products",
        "entity": "Product",
        "entity_lower": "product",
        "entity_plural": "Products",
        "route_prefix": "/products",
        "fields": [
            ("id", "number"),
            ("name", "string"),
            ("price", "number"),
            ("stock", "number"),
            ("available", "boolean"),
            ("updatedAt", "Date"),
        ],
        "optional_fields": ["stock", "updatedAt"],
        "sample_values": {
            "id": "42",
            "name": '"Widget Pro"',
            "price": "19.99",
            "stock": "100",
            "available": "true",
            "updatedAt": "new Date()",
        },
    },
    {
        "name": "orders",
        "entity": "Order",
        "entity_lower": "order",
        "entity_plural": "Orders",
        "route_prefix": "/orders",
        "fields": [
            ("id", "number"),
            ("customerId", "number"),
            ("total", "number"),
            ("status", "string"),
            ("paid", "boolean"),
            ("placedAt", "Date"),
        ],
        "optional_fields": ["paid", "placedAt"],
        "sample_values": {
            "id": "7",
            "customerId": "3",
            "total": "99.50",
            "status": '"pending"',
            "paid": "false",
            "placedAt": "new Date()",
        },
    },
    {
        "name": "invoices",
        "entity": "Invoice",
        "entity_lower": "invoice",
        "entity_plural": "Invoices",
        "route_prefix": "/invoices",
        "fields": [
            ("id", "number"),
            ("amount", "number"),
            ("currency", "string"),
            ("dueDate", "Date"),
            ("settled", "boolean"),
            ("reference", "string"),
        ],
        "optional_fields": ["settled", "reference"],
        "sample_values": {
            "id": "55",
            "amount": "250.00",
            "currency": '"USD"',
            "dueDate": "new Date()",
            "settled": "false",
            "reference": '"INV-2024-055"',
        },
    },
    {
        "name": "events",
        "entity": "Event",
        "entity_lower": "event",
        "entity_plural": "Events",
        "route_prefix": "/events",
        "fields": [
            ("id", "number"),
            ("title", "string"),
            ("capacity", "number"),
            ("startTime", "Date"),
            ("published", "boolean"),
            ("venue", "string"),
        ],
        "optional_fields": ["capacity", "venue"],
        "sample_values": {
            "id": "12",
            "title": '"Annual Conference"',
            "capacity": "500",
            "startTime": "new Date()",
            "published": "true",
            "venue": '"Convention Center"',
        },
    },
]

MISMATCH_KEYS = [
    "wrong_field_name",
    "wrong_primitive_type",
    "optional_as_required",
    "missing_required_field",
    "wrong_return_type",
    "date_as_string",
]


class Generator(TaskGenerator):
    task_id = "TS1_type_mismatch"
    domain = "SWE"
    difficulty = "hard"
    languages = ["typescript"]

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)
        domain = DOMAINS[seed % len(DOMAINS)]

        # Select 4-6 mismatches (deduplicated)
        num_mismatches = rng.randint(4, 6)
        selected_keys = rng.sample(MISMATCH_KEYS, num_mismatches)

        mismatches = self._build_mismatches(rng, domain, selected_keys)

        workspace_files = {
            "types.ts": self._gen_types(domain),
            "handlers.ts": self._gen_handlers(domain, mismatches),
            "service.ts": self._gen_service(domain, mismatches),
            "test.ts": self._gen_tests(domain),
            "tsconfig.json": self._gen_tsconfig(),
            "package.json": self._gen_package_json(domain),
        }

        spec_md = self._gen_spec(domain, mismatches)
        brief_md = self._gen_brief(domain)

        return GeneratedTask(
            task_id=self.task_id,
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected={
                "seed": seed,
                "domain": domain["name"],
                "entity": domain["entity"],
                "num_mismatches": len(mismatches),
                "mismatch_keys": [m["key"] for m in mismatches],
                "checks": [
                    "tsc_no_errors",
                    "handler_return_types_correct",
                    "service_field_types_correct",
                    "optional_fields_handled",
                    "required_fields_present",
                    "tests_pass",
                ],
            },
            workspace_files=workspace_files,
            metadata={"difficulty": "hard", "category": "SWE"},
        )

    # ── Mismatch construction ─────────────────────────────────────────────────

    def _build_mismatches(self, rng: SeededRandom, domain: dict, keys: list) -> list:
        """Build concrete mismatch instances for selected keys and domain."""
        fields = domain["fields"]
        optional_fields = domain["optional_fields"]
        entity = domain["entity"]
        mismatches = []

        for key in keys:
            if key == "wrong_field_name":
                candidates = [(n, t) for n, t in fields if n != "id"]
                field_name, field_type = rng.choice(candidates)
                # Create a plausible-but-wrong name
                if field_name.endswith("At"):
                    wrong_name = field_name[:-2] + "Time"
                elif field_name[0].islower() and len(field_name) > 3:
                    wrong_name = field_name + "Val"
                else:
                    wrong_name = field_name + "Value"
                mismatches.append({
                    "key": key,
                    "layer": "handler",
                    "field": field_name,
                    "wrong_name": wrong_name,
                    "correct_name": field_name,
                    "field_type": field_type,
                    "description": (
                        f"In `handlers.ts`, the `create{entity}Handler` function "
                        f"destructures `{wrong_name}` from the request body, but "
                        f"`types.ts` defines the field as `{field_name}: {field_type}`. "
                        f"Fix: rename the destructured variable from `{wrong_name}` to `{field_name}`."
                    ),
                })

            elif key == "wrong_primitive_type":
                # Find a number field to mis-annotate as string in the service
                candidates = [(n, t) for n, t in fields if t == "number" and n != "id"]
                if not candidates:
                    candidates = [(n, t) for n, t in fields if t == "string"]
                field_name, field_type = rng.choice(candidates)
                wrong_type = "string" if field_type == "number" else "number"
                mismatches.append({
                    "key": key,
                    "layer": "service",
                    "field": field_name,
                    "wrong_type": wrong_type,
                    "correct_type": field_type,
                    "description": (
                        f"In `service.ts`, the internal `Stored{entity}` type "
                        f"declares `{field_name}: {wrong_type}`, but "
                        f"`types.ts` defines `{field_name}: {field_type}`. "
                        f"Fix: change the annotation to `{field_name}: {field_type}`."
                    ),
                })

            elif key == "optional_as_required":
                if optional_fields:
                    field_name = rng.choice(optional_fields)
                    field_type = next(t for n, t in fields if n == field_name)
                    mismatches.append({
                        "key": key,
                        "layer": "handler",
                        "field": field_name,
                        "field_type": field_type,
                        "description": (
                            f"In `handlers.ts`, the `get{entity}Handler` function "
                            f"calls `result.{field_name}.toString()` without checking "
                            f"for `undefined`, but `types.ts` declares "
                            f"`{field_name}?: {field_type}` (optional). "
                            f"Fix: use optional chaining: "
                            f"`result.{field_name}?.toString() ?? ''`."
                        ),
                    })

            elif key == "missing_required_field":
                required = [
                    (n, t) for n, t in fields
                    if n not in optional_fields and n != "id" and t != "Date"
                ]
                if required:
                    field_name, field_type = rng.choice(required)
                    mismatches.append({
                        "key": key,
                        "layer": "service",
                        "field": field_name,
                        "field_type": field_type,
                        "description": (
                            f"In `service.ts`, the `listAll` function returns object "
                            f"literals that omit the required `{field_name}: {field_type}` "
                            f"field defined in `types.ts`. "
                            f"Fix: add `{field_name}` to every returned object literal "
                            f"in the seed-data array."
                        ),
                    })

            elif key == "wrong_return_type":
                candidates = [(n, t) for n, t in fields if t in ("number", "string") and n != "id"]
                if candidates:
                    field_name, field_type = rng.choice(candidates)
                    wrong_ret = "string" if field_type == "number" else "number"
                    mismatches.append({
                        "key": key,
                        "layer": "handler",
                        "field": field_name,
                        "wrong_return": wrong_ret,
                        "correct_return": field_type,
                        "description": (
                            f"In `handlers.ts`, the `extract{field_name[0].upper() + field_name[1:]}` "
                            f"helper is annotated with return type `{wrong_ret}` but the "
                            f"implementation returns a `{field_type}` value (matching "
                            f"`{field_name}: {field_type}` in `types.ts`). "
                            f"Fix: change the return type annotation from `{wrong_ret}` to `{field_type}`."
                        ),
                    })

            elif key == "date_as_string":
                date_fields = [(n, t) for n, t in fields if t == "Date"]
                if date_fields:
                    field_name, _ = rng.choice(date_fields)
                    mismatches.append({
                        "key": key,
                        "layer": "service",
                        "field": field_name,
                        "description": (
                            f"In `service.ts`, the `create` function sets "
                            f"`{field_name}: new Date().toISOString()` which produces a "
                            f"`string`, but `types.ts` declares `{field_name}: Date`. "
                            f"Fix: use `{field_name}: new Date()` (remove `.toISOString()`)."
                        ),
                    })

        return mismatches

    # ── types.ts ──────────────────────────────────────────────────────────────

    def _gen_types(self, domain: dict) -> str:
        entity = domain["entity"]
        fields = domain["fields"]
        optional_fields = domain["optional_fields"]
        entity_plural = domain["entity_plural"]

        field_lines = []
        for name, typ in fields:
            opt = "?" if name in optional_fields else ""
            field_lines.append(f"  {name}{opt}: {typ};")
        fields_block = "\n".join(field_lines)

        create_lines = []
        for name, typ in fields:
            if name in ("id",):
                continue
            # skip auto-assigned timestamp fields
            if name in ("createdAt", "updatedAt", "placedAt"):
                continue
            opt = "?" if name in optional_fields else ""
            create_lines.append(f"  {name}{opt}: {typ};")
        create_block = "\n".join(create_lines)

        return (
            "/**\n"
            f" * types.ts — Shared type definitions for the {domain['name']} API.\n"
            " * This file is the source of truth for all interface shapes.\n"
            " * Do NOT modify this file.\n"
            " */\n"
            "\n"
            f"export interface {entity} {{\n"
            f"{fields_block}\n"
            "}\n"
            "\n"
            f"export interface Create{entity}Request {{\n"
            f"{create_block}\n"
            "}\n"
            "\n"
            f"export interface {entity_plural}Response {{\n"
            f"  items: {entity}[];\n"
            "  total: number;\n"
            "}\n"
            "\n"
            "export interface ApiResponse<T> {\n"
            "  data: T;\n"
            "  success: boolean;\n"
            "  message?: string;\n"
            "}\n"
        )

    # ── handlers.ts ──────────────────────────────────────────────────────────

    def _gen_handlers(self, domain: dict, mismatches: list) -> str:
        entity = domain["entity"]
        entity_lower = domain["entity_lower"]
        fields = domain["fields"]
        optional_fields = domain["optional_fields"]
        entity_plural = domain["entity_plural"]

        # Index handler-layer mismatches by key
        hm = {m["key"]: m for m in mismatches if m.get("layer") in ("handler", "both")}

        # --- create handler: destructure block ---
        create_fields = [
            (n, t) for n, t in fields
            if n not in ("id", "createdAt", "updatedAt", "placedAt")
        ]
        destructure_parts = []
        for name, _ in create_fields:
            if "wrong_field_name" in hm and hm["wrong_field_name"]["field"] == name:
                destructure_parts.append(hm["wrong_field_name"]["wrong_name"])
            else:
                destructure_parts.append(name)
        destructure_str = ", ".join(destructure_parts)

        assign_lines = []
        for name, _ in create_fields:
            if "wrong_field_name" in hm and hm["wrong_field_name"]["field"] == name:
                wrong = hm["wrong_field_name"]["wrong_name"]
                assign_lines.append(
                    f"    {name}: {wrong},  // BUG: variable is '{wrong}', types.ts expects '{name}'"
                )
            else:
                assign_lines.append(f"    {name},")
        assign_block = "\n".join(assign_lines)

        # --- get handler: optional field access ---
        opt_field = optional_fields[0] if optional_fields else None
        if "optional_as_required" in hm and opt_field:
            # BUG: no null check
            opt_line = (
                f"  // BUG: {opt_field} is optional in types.ts but accessed without null check\n"
                f"  const display = result.{opt_field}.toString();"
            )
        elif opt_field:
            opt_line = f"  const display = result.{opt_field}?.toString() ?? '';"
        else:
            opt_line = "  const display = '';"

        # --- extract helper ---
        extract_snippet = ""
        if "wrong_return_type" in hm:
            m = hm["wrong_return_type"]
            fname = m["field"]
            wrong_ret = m["wrong_return"]
            correct_ret = m["correct_return"]
            cap = fname[0].upper() + fname[1:]
            extract_snippet = (
                f"\n// Helper: extract {fname} value from a raw data object\n"
                f"// BUG: return type annotation is wrong — should be {correct_ret}, not {wrong_ret}\n"
                f"function extract{cap}(raw: Record<string, unknown>): {wrong_ret} {{\n"
                f"  return raw['{fname}'] as {correct_ret};\n"
                f"}}\n"
            )
        else:
            # Include a correct extract helper if any suitable field exists
            candidates = [(n, t) for n, t in fields if t in ("number", "string") and n != "id"]
            if candidates:
                fname, ftype = candidates[0]
                cap = fname[0].upper() + fname[1:]
                extract_snippet = (
                    f"\n// Helper: extract {fname} value from a raw data object\n"
                    f"function extract{cap}(raw: Record<string, unknown>): {ftype} {{\n"
                    f"  return raw['{fname}'] as {ftype};\n"
                    f"}}\n"
                )

        return (
            f"import {{ {entity}, Create{entity}Request, ApiResponse, {entity_plural}Response }} from './types';\n"
            f"import {{ {entity_lower}Service }} from './service';\n"
            "\n"
            "/**\n"
            f" * handlers.ts — Route handlers for the {domain['name']} API.\n"
            " * Handles HTTP request parsing and delegates to the service layer.\n"
            " */\n"
            f"{extract_snippet}\n"
            f"export async function create{entity}Handler(\n"
            f"  body: Create{entity}Request\n"
            f"): Promise<ApiResponse<{entity}>> {{\n"
            f"  const {{ {destructure_str} }} = body;\n"
            "\n"
            f"  const result = await {entity_lower}Service.create({{\n"
            "    id: 0,  // assigned by service\n"
            f"{assign_block}\n"
            "  } as any);\n"
            "\n"
            "  return {\n"
            "    data: result,\n"
            "    success: true,\n"
            f"    message: '{entity} created',\n"
            "  };\n"
            "}\n"
            "\n"
            f"export async function get{entity}Handler(id: number): Promise<ApiResponse<{entity}>> {{\n"
            f"  const result = await {entity_lower}Service.findById(id);\n"
            "\n"
            f"{opt_line}\n"
            "\n"
            "  return {\n"
            "    data: result,\n"
            "    success: true,\n"
            "    message: display,\n"
            "  };\n"
            "}\n"
            "\n"
            f"export async function list{entity}sHandler(\n"
            "  page: number = 1,\n"
            "  limit: number = 20\n"
            f"): Promise<ApiResponse<{entity_plural}Response>> {{\n"
            f"  const items = await {entity_lower}Service.listAll(page, limit);\n"
            "\n"
            "  return {\n"
            "    data: {\n"
            "      items,\n"
            "      total: items.length,\n"
            "    },\n"
            "    success: true,\n"
            "  };\n"
            "}\n"
            "\n"
            f"export async function delete{entity}Handler(id: number): Promise<ApiResponse<boolean>> {{\n"
            f"  const deleted = await {entity_lower}Service.remove(id);\n"
            "  return {\n"
            "    data: deleted,\n"
            "    success: true,\n"
            f"    message: deleted ? '{entity} deleted' : '{entity} not found',\n"
            "  };\n"
            "}\n"
        )

    # ── service.ts ────────────────────────────────────────────────────────────

    def _gen_service(self, domain: dict, mismatches: list) -> str:
        entity = domain["entity"]
        entity_lower = domain["entity_lower"]
        fields = domain["fields"]
        optional_fields = domain["optional_fields"]
        entity_plural = domain["entity_plural"]

        # Index service-layer mismatches by key
        sm = {m["key"]: m for m in mismatches if m.get("layer") in ("service", "both")}

        # --- buildRecord helper: explicit return type annotation triggers wrong_primitive_type ---
        # The helper builds a partial record; its return type annotation is what we mis-type.
        build_ret_lines = []
        for name, typ in fields:
            if name in ("id",):
                continue
            if "wrong_primitive_type" in sm and sm["wrong_primitive_type"]["field"] == name:
                wrong = sm["wrong_primitive_type"]["wrong_type"]
                build_ret_lines.append(
                    f"  {name}: {wrong};  // BUG: types.ts declares {name}: {typ}"
                )
            else:
                opt = "?" if name in optional_fields else ""
                build_ret_lines.append(f"  {name}{opt}: {typ};")
        build_ret_block = "\n".join(build_ret_lines)

        # --- buildRecord function body (always returns correct values) ---
        build_body_lines = []
        for name, typ in fields:
            if name == "id":
                continue
            if typ == "Date":
                if "date_as_string" in sm and sm["date_as_string"]["field"] == name:
                    # BUG: assign string to Date field — surfaces as error against Entity type
                    build_body_lines.append(
                        f"    {name}: new Date().toISOString(),  // BUG: string assigned to Date field"
                    )
                else:
                    build_body_lines.append(f"    {name}: new Date(),")
            elif typ == "number":
                build_body_lines.append(f"    {name}: typeof src.{name} === 'number' ? src.{name} : Number(src.{name}),")
            elif typ == "string":
                build_body_lines.append(f"    {name}: String(src.{name} ?? ''),")
            elif typ == "boolean":
                build_body_lines.append(f"    {name}: Boolean(src.{name}),")
            else:
                build_body_lines.append(f"    {name}: src.{name},")
        build_body_block = "\n".join(build_body_lines)

        # --- create function body ---
        create_lines = []
        for name, typ in fields:
            if name == "id":
                create_lines.append("      id: Math.floor(Math.random() * 90000) + 10000,")
            else:
                create_lines.append(f"      ...fields,")
                break  # spread fields from buildRecord result
        # If we didn't hit the else branch (all fields are id), handle gracefully
        if not any("...fields" in l for l in create_lines):
            create_lines.append("      ...fields,")
        create_block = "\n".join(create_lines)

        # --- listAll seed data (missing_required_field) ---
        # Returns an explicitly typed array — omitting a required field is a real tsc error
        list_lines = []
        for name, typ in fields:
            if "missing_required_field" in sm and sm["missing_required_field"]["field"] == name:
                list_lines.append(
                    f"        // BUG: '{name}' omitted — required by {entity} interface in types.ts"
                )
            elif name == "id":
                list_lines.append("        id: i + 1,")
            elif typ == "Date":
                list_lines.append(f"        {name}: new Date(Date.now() - i * 86400000),")
            elif typ == "number":
                list_lines.append(f"        {name}: (i + 1) * 10,")
            elif typ == "string":
                list_lines.append(f"        {name}: `{entity_lower}-sample-${{i + 1}}`,")
            elif typ == "boolean":
                list_lines.append(f"        {name}: i % 2 === 0,")
        list_block = "\n".join(list_lines)

        return (
            f"import {{ {entity} }} from './types';\n"
            "\n"
            "/**\n"
            f" * service.ts — Business logic for the {domain['name']} service.\n"
            " * Handles data transformation and persistence operations.\n"
            " */\n"
            "\n"
            "// In-memory store\n"
            f"const store: Map<number, {entity}> = new Map();\n"
            "\n"
            f"// buildRecord: construct field values from raw input.\n"
            f"// Return type must match Omit<{entity}, 'id'>.\n"
            f"function build{entity}Record(src: Partial<{entity}>): {{\n"
            f"{build_ret_block}\n"
            "} {\n"
            "  return {\n"
            f"{build_body_block}\n"
            "  };\n"
            "}\n"
            "\n"
            f"export const {entity_lower}Service = {{\n"
            f"  async create({entity_lower}: Omit<{entity}, 'id'>): Promise<{entity}> {{\n"
            f"    const fields = build{entity}Record({entity_lower});\n"
            f"    const created: {entity} = {{\n"
            f"{create_block}\n"
            "    };\n"
            f"    store.set(created.id, created);\n"
            "    return created;\n"
            "  },\n"
            "\n"
            f"  async findById(id: number): Promise<{entity}> {{\n"
            "    const item = store.get(id);\n"
            "    if (!item) {\n"
            f"      throw new Error(`{entity} ${{id}} not found`);\n"
            "    }\n"
            "    return item;\n"
            "  },\n"
            "\n"
            f"  async listAll(page: number, limit: number): Promise<{entity}[]> {{\n"
            "    const all = Array.from(store.values());\n"
            "    if (all.length === 0) {\n"
            "      // Return seed data when store is empty\n"
            f"      const seedData: {entity}[] = Array.from({{ length: 3 }}, (_, i) => ({{\n"
            f"{list_block}\n"
            "      }));\n"
            "      return seedData;\n"
            "    }\n"
            "    const start = (page - 1) * limit;\n"
            "    return all.slice(start, start + limit);\n"
            "  },\n"
            "\n"
            "  async remove(id: number): Promise<boolean> {\n"
            "    return store.delete(id);\n"
            "  },\n"
            "\n"
            "  async count(): Promise<number> {\n"
            "    return store.size;\n"
            "  },\n"
            "};\n"
        )

    # ── test.ts ───────────────────────────────────────────────────────────────

    def _gen_tests(self, domain: dict) -> str:
        entity = domain["entity"]
        entity_lower = domain["entity_lower"]
        entity_plural = domain["entity_plural"]
        fields = domain["fields"]
        optional_fields = domain["optional_fields"]
        sample = domain["sample_values"]

        # Build a create payload (no id, no auto-timestamp fields, no optionals)
        payload_parts = []
        for name, typ in fields:
            if name in ("id", "createdAt", "updatedAt", "placedAt"):
                continue
            if name in optional_fields:
                continue
            val = sample.get(name, '"test"')
            payload_parts.append(f"  {name}: {val},")
        payload_block = "\n".join(payload_parts)

        # First non-id, non-date required field for assertion
        check_field = next(
            (n for n, t in fields
             if n not in optional_fields and n != "id" and t != "Date"),
            fields[1][0] if len(fields) > 1 else "id",
        )
        check_val = sample.get(check_field, '"test"')

        # type-level object literal for the interface check
        type_literal_parts = []
        for name, typ in fields:
            val = sample.get(name, '"test"' if typ == "string" else "0")
            type_literal_parts.append(f"  {name}: {val},")
        type_literal_block = "\n".join(type_literal_parts)

        return (
            "/**\n"
            f" * test.ts — Type-level and runtime tests for the {domain['name']} API.\n"
            " *\n"
            " * Run:\n"
            " *   npx tsc --noEmit   # must exit 0\n"
            " *   npx ts-node test.ts  # must exit 0\n"
            " */\n"
            "\n"
            f"import {{ {entity}, ApiResponse, {entity_plural}Response }} from './types';\n"
            "import {\n"
            f"  create{entity}Handler,\n"
            f"  get{entity}Handler,\n"
            f"  list{entity}sHandler,\n"
            f"  delete{entity}Handler,\n"
            "} from './handlers';\n"
            "\n"
            "// ── Compile-time type checks ─────────────────────────────────────────────────\n"
            "\n"
            f"// Verify {entity} interface is structurally complete\n"
            f"const _typeCheck: {entity} = {{\n"
            f"{type_literal_block}\n"
            "};\n"
            "void _typeCheck;\n"
            "\n"
            "// Verify handler return types are compatible\n"
            f"async function _checkHandlerTypes(): Promise<void> {{\n"
            f"  const r1: ApiResponse<{entity}> = await create{entity}Handler({{\n"
            f"{payload_block}\n"
            "  });\n"
            f"  const _id: number = r1.data.id;\n"
            "  void _id;\n"
            "\n"
            f"  const r2: ApiResponse<{entity_plural}Response> = await list{entity}sHandler(1, 10);\n"
            f"  const _items: {entity}[] = r2.data.items;\n"
            "  void _items;\n"
            "}\n"
            "void _checkHandlerTypes;\n"
            "\n"
            "// ── Runtime assertions ───────────────────────────────────────────────────────\n"
            "\n"
            "let passed = 0;\n"
            "let failed = 0;\n"
            "\n"
            "function assert(condition: boolean, message: string): void {\n"
            "  if (condition) {\n"
            "    console.log(`  PASS  ${message}`);\n"
            "    passed++;\n"
            "  } else {\n"
            "    console.error(`  FAIL  ${message}`);\n"
            "    failed++;\n"
            "  }\n"
            "}\n"
            "\n"
            "async function runTests(): Promise<void> {\n"
            f"  console.log('Running {entity} handler tests...');\n"
            "\n"
            f"  // T1: create{entity}Handler returns entity with correct shape\n"
            f"  const created = await create{entity}Handler({{\n"
            f"{payload_block}\n"
            "  });\n"
            f"  assert(created.success === true, 'create{entity}: success is true');\n"
            f"  assert(typeof created.data.id === 'number', 'create{entity}: id is a number');\n"
            f"  assert(created.data.{check_field} === {check_val}, 'create{entity}: {check_field} matches input');\n"
            "\n"
            f"  // T2: list{entity}sHandler returns typed response\n"
            f"  const listed = await list{entity}sHandler(1, 10);\n"
            f"  assert(listed.success === true, 'list{entity}s: success is true');\n"
            f"  assert(Array.isArray(listed.data.items), 'list{entity}s: items is an array');\n"
            f"  assert(typeof listed.data.total === 'number', 'list{entity}s: total is a number');\n"
            "\n"
            f"  // T3: get{entity}Handler returns the created entity\n"
            f"  const fetched = await get{entity}Handler(created.data.id);\n"
            f"  assert(fetched.success === true, 'get{entity}: success is true');\n"
            f"  assert(fetched.data.id === created.data.id, 'get{entity}: id matches');\n"
            "\n"
            f"  // T4: delete{entity}Handler removes the entity\n"
            f"  const deleted = await delete{entity}Handler(created.data.id);\n"
            f"  assert(deleted.success === true, 'delete{entity}: success is true');\n"
            f"  assert(deleted.data === true, 'delete{entity}: returns true');\n"
            "}\n"
            "\n"
            "runTests().then(() => {\n"
            "  console.log(`\\n${passed} passed, ${failed} failed`);\n"
            "  if (failed > 0) process.exit(1);\n"
            "}).catch((err) => {\n"
            "  console.error('Test suite error:', err);\n"
            "  process.exit(1);\n"
            "});\n"
        )

    # ── tsconfig.json ─────────────────────────────────────────────────────────

    def _gen_tsconfig(self) -> str:
        return (
            "{\n"
            '  "compilerOptions": {\n'
            '    "target": "ES2020",\n'
            '    "module": "commonjs",\n'
            '    "lib": ["ES2020"],\n'
            '    "strict": true,\n'
            '    "noImplicitAny": true,\n'
            '    "strictNullChecks": true,\n'
            '    "noUnusedLocals": false,\n'
            '    "noUnusedParameters": false,\n'
            '    "esModuleInterop": true,\n'
            '    "outDir": "./dist",\n'
            '    "rootDir": "./"\n'
            "  },\n"
            '  "include": ["*.ts"],\n'
            '  "exclude": ["dist", "node_modules"]\n'
            "}\n"
        )

    # ── package.json ──────────────────────────────────────────────────────────

    def _gen_package_json(self, domain: dict) -> str:
        return (
            "{\n"
            f'  "name": "{domain["name"]}-api",\n'
            '  "version": "1.0.0",\n'
            f'  "description": "{domain["entity"]} REST API with TypeScript type definitions",\n'
            '  "scripts": {\n'
            '    "typecheck": "tsc --noEmit",\n'
            '    "test": "tsc --noEmit && ts-node test.ts",\n'
            '    "build": "tsc"\n'
            "  },\n"
            '  "devDependencies": {\n'
            '    "typescript": "^5.0.0",\n'
            '    "ts-node": "^10.9.0"\n'
            "  }\n"
            "}\n"
        )

    # ── spec.md ───────────────────────────────────────────────────────────────

    def _gen_spec(self, domain: dict, mismatches: list) -> str:
        entity = domain["entity"]
        num = len(mismatches)

        mismatch_sections = []
        for i, m in enumerate(mismatches, 1):
            key_title = m["key"].replace("_", " ").title()
            mismatch_sections.append(
                f"### Mismatch {i}: {key_title}\n\n{m['description']}"
            )
        mismatch_block = "\n\n".join(mismatch_sections)

        return (
            f"# TS1_type_mismatch: {entity} API Type Errors\n"
            "\n"
            "## Goal\n"
            "\n"
            f"Fix all TypeScript type mismatches in the `{domain['name']}` API so that\n"
            "`npx tsc --noEmit` exits with code 0 and all runtime tests in `test.ts` pass.\n"
            "\n"
            "## Background\n"
            "\n"
            "The workspace has three editable source files and two read-only files:\n"
            "\n"
            f"- **`types.ts`** — Shared interface definitions. **Source of truth. Do NOT modify.**\n"
            f"- **`handlers.ts`** — HTTP handler layer. Contains type mismatches.\n"
            f"- **`service.ts`** — Business logic layer. Contains type mismatches.\n"
            f"- **`test.ts`** — Type-level and runtime tests. **Do NOT modify.**\n"
            f"- **`tsconfig.json`** — TypeScript config (`strict: true`). **Do NOT modify.**\n"
            "\n"
            f"## Type Mismatches to Fix ({num} total)\n"
            "\n"
            f"`types.ts` is always correct. Fix `handlers.ts` and/or `service.ts` to match.\n"
            "\n"
            f"{mismatch_block}\n"
            "\n"
            "## Requirements\n"
            "\n"
            "1. `npx tsc --noEmit` must exit with code `0` (zero TypeScript errors).\n"
            "2. `npx ts-node test.ts` must exit with code `0` (all assertions pass).\n"
            "3. **Do NOT modify** `types.ts`, `test.ts`, or `tsconfig.json`.\n"
            "4. Do not add `// @ts-ignore` or `// @ts-expect-error` suppressions.\n"
            "5. Only edit `handlers.ts` and `service.ts`.\n"
            "\n"
            "## File Map\n"
            "\n"
            "| File | Action |\n"
            "|------|--------|\n"
            "| `types.ts` | **Read-only** — source of truth |\n"
            "| `handlers.ts` | Fix handler-layer type mismatches |\n"
            "| `service.ts` | Fix service-layer type mismatches |\n"
            "| `test.ts` | **Read-only** — do not modify |\n"
            "| `tsconfig.json` | **Read-only** — do not modify |\n"
            "\n"
            "## Verification\n"
            "\n"
            "```bash\n"
            "cd /workspace\n"
            "npm install\n"
            "npx tsc --noEmit        # must exit 0\n"
            "npx ts-node test.ts     # must exit 0\n"
            "```\n"
        )

    # ── brief.md ──────────────────────────────────────────────────────────────

    def _gen_brief(self, domain: dict) -> str:
        entity = domain["entity"]
        return (
            f"# TS1_type_mismatch: Fix TypeScript Type Errors (Brief)\n"
            "\n"
            f"The `{domain['name']}` API has TypeScript type errors between the shared\n"
            f"type definitions (`types.ts`) and the implementations in `handlers.ts`\n"
            "and `service.ts`.\n"
            "\n"
            "Fix the type errors so the following both pass:\n"
            "\n"
            "```bash\n"
            "cd /workspace\n"
            "npm install\n"
            "npx tsc --noEmit     # must exit 0\n"
            "npx ts-node test.ts  # must exit 0\n"
            "```\n"
            "\n"
            "**Do NOT modify** `types.ts`, `test.ts`, or `tsconfig.json`.\n"
            "Only modify `handlers.ts` and `service.ts`.\n"
            "\n"
            "Follow the Planner's guidance precisely.\n"
        )
