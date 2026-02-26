"""
Parameterized generator for IR3: Multi-Source Cross-Reference QA.

Each seed produces:
  - A domain (project_report, company_audit, research_review, policy_analysis)
  - 5-7 corpus documents, each authoritative for specific topics
  - doc_E is always OUTDATED and must be ignored for budget/financial figures
  - Some documents contain contradictory information; only the authoritative
    source should be used for each topic
  - 6-10 questions spanning multiple topics requiring cross-doc reasoning
  - workspace/answer.json (blank template with all questions)
  - expected.json with correct answers keyed to authoritative sources

TNI Pattern A (Hidden Constraints): The spec explicitly defines an authority
hierarchy. The brief vaguely says "answer questions from the corpus." Agents
must read the spec carefully to know which document is authoritative for each
topic and avoid answers from non-authoritative (especially outdated) sources.
"""
from __future__ import annotations

import json
from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom, NamePool, PROJECT_NAMES

# ── Domain configurations ────────────────────────────────────────────────────

DOMAINS = [
    {
        "id": "project_report",
        "label": "Project Status Report",
        "org": "Meridian Technologies",
        "topics": {
            "financial": "doc_A.txt",   # budget figures
            "technical": "doc_B.txt",   # technical specs / architecture
            "personnel": "doc_C.txt",   # team / staffing
            "timeline":  "doc_D.txt",   # milestones / dates
        },
        "outdated_doc": "doc_E.txt",
        "outdated_reason": "preliminary budget estimate superseded by board approval",
    },
    {
        "id": "company_audit",
        "label": "Annual Company Audit",
        "org": "Vanguard Capital Group",
        "topics": {
            "financial": "doc_A.txt",
            "technical": "doc_B.txt",
            "personnel": "doc_C.txt",
            "timeline":  "doc_D.txt",
        },
        "outdated_doc": "doc_E.txt",
        "outdated_reason": "draft figures that were revised before final audit submission",
    },
    {
        "id": "research_review",
        "label": "Research Program Review",
        "org": "Apex Research Institute",
        "topics": {
            "financial": "doc_A.txt",
            "technical": "doc_B.txt",
            "personnel": "doc_C.txt",
            "timeline":  "doc_D.txt",
        },
        "outdated_doc": "doc_E.txt",
        "outdated_reason": "early grant estimate that was superseded by the approved budget",
    },
    {
        "id": "policy_analysis",
        "label": "Policy Impact Analysis",
        "org": "Solaris Policy Foundation",
        "topics": {
            "financial": "doc_A.txt",
            "technical": "doc_B.txt",
            "personnel": "doc_C.txt",
            "timeline":  "doc_D.txt",
        },
        "outdated_doc": "doc_E.txt",
        "outdated_reason": "pre-revision cost model that is no longer valid",
    },
]

# ── Fact pools for each topic area ──────────────────────────────────────────

ARCHITECTURES = [
    ("microservices", "gRPC", "Kubernetes", "PostgreSQL"),
    ("monolith", "REST/JSON", "Docker Swarm", "MySQL"),
    ("event-driven", "Apache Kafka", "Nomad", "CockroachDB"),
    ("serverless", "GraphQL", "AWS Lambda", "DynamoDB"),
    ("hybrid mesh", "WebSocket", "ECS Fargate", "Cassandra"),
]

TECH_VERSIONS = [
    ("Python 3.12", "FastAPI 0.111", "React 18.3", "Node 22"),
    ("Go 1.22", "Gin 1.9", "Vue 3.4", "Bun 1.1"),
    ("Java 21", "Spring Boot 3.2", "Angular 17", "Deno 2"),
    ("Rust 1.78", "Axum 0.7", "Svelte 5", "Bun 1.2"),
    ("TypeScript 5.4", "Hono 4.2", "Nuxt 3.11", "Node 20"),
]

MILESTONES = [
    [("Design freeze",  "2025-03-01"), ("Alpha release", "2025-06-15"),
     ("Beta launch",    "2025-09-01"), ("GA release",    "2025-12-01")],
    [("Kick-off",       "2025-01-15"), ("MVP delivery",  "2025-05-30"),
     ("User testing",   "2025-08-15"), ("Production",    "2025-11-30")],
    [("Requirements",   "2025-02-01"), ("Prototype",     "2025-05-01"),
     ("Pilot",          "2025-08-01"), ("Full rollout",  "2025-11-01")],
    [("Inception",      "2025-03-10"), ("Dev complete",  "2025-07-01"),
     ("QA sign-off",    "2025-09-15"), ("Launch",        "2025-12-15")],
    [("Planning",       "2025-02-20"), ("Sprint 1 done", "2025-04-30"),
     ("Integration",    "2025-07-15"), ("Deploy",        "2025-10-31")],
]

TEAM_SIZES = [12, 18, 24, 9, 31, 15, 22]
CONTRACTOR_COUNTS = [3, 5, 7, 2, 8, 4, 6]
DEPARTMENTS_LIST = [
    ["Engineering", "Product", "QA"],
    ["Research", "Development", "Operations"],
    ["Architecture", "Platform", "Security"],
    ["Data Science", "Infrastructure", "DevOps"],
    ["Backend", "Frontend", "SRE"],
]

BUDGETS_M = [4.2, 7.8, 12.5, 3.9, 18.0, 6.1, 9.4, 15.3, 5.7, 11.2]
OUTDATED_BUDGETS_M = [2.1, 5.5, 8.0, 2.4, 11.0, 3.8, 6.0, 9.9, 3.2, 7.0]

FISCAL_YEARS = [2024, 2025, 2026]
QUARTERS = ["Q1", "Q2", "Q3", "Q4"]


class Generator(TaskGenerator):
    task_id = "IR3_multi_source"
    domain = "information_retrieval"
    difficulty = "hard"
    languages = ["json"]

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)
        names = NamePool(seed + 7, count=40)

        # ── Pick domain ──────────────────────────────────────────────────────
        domain_cfg = rng.choice(DOMAINS)
        org = domain_cfg["org"]
        label = domain_cfg["label"]
        outdated_doc = domain_cfg["outdated_doc"]  # always doc_E.txt
        outdated_reason = domain_cfg["outdated_reason"]

        # ── Pick project ─────────────────────────────────────────────────────
        project = rng.choice(PROJECT_NAMES)
        fy = rng.choice(FISCAL_YEARS)
        quarter = rng.choice(QUARTERS)

        # ── Pick facts ───────────────────────────────────────────────────────
        arch_tuple = rng.choice(ARCHITECTURES)
        arch_style, rpc_proto, orchestrator, db_engine = arch_tuple

        tech_tuple = rng.choice(TECH_VERSIONS)
        lang, framework, frontend, runtime = tech_tuple

        milestones = rng.choice(MILESTONES)
        # Pick a random milestone subset (4 milestones always present)
        ga_date = milestones[-1][1]

        team_size = rng.choice(TEAM_SIZES)
        contractors = rng.choice(CONTRACTOR_COUNTS)
        departments = rng.choice(DEPARTMENTS_LIST)

        # Budget: doc_A has the real budget; doc_E has outdated (lower) figure
        budget_true = rng.choice(BUDGETS_M)
        # Ensure outdated budget differs and is lower
        outdated_budget = round(budget_true * rng.uniform(0.45, 0.72), 1)

        # Personnel leads
        lead_name = names.next()
        tech_lead = names.next()
        pm_name = names.next()
        qa_lead = names.next()
        security_lead = names.next()
        dep1_head = names.next()
        dep2_head = names.next()
        dep3_head = names.next()

        # Doc counts (5-7 docs depending on seed)
        n_docs = rng.randint(5, 7)
        # Always have A-E; F and G are optional supplementary
        include_doc_f = n_docs >= 6
        include_doc_g = n_docs >= 7

        # ── Generate doc contents ─────────────────────────────────────────────
        doc_a = self._gen_doc_a(org, project, fy, quarter, budget_true, lead_name, pm_name)
        doc_b = self._gen_doc_b(org, project, arch_style, rpc_proto, orchestrator,
                                 db_engine, lang, framework, frontend, runtime, tech_lead)
        doc_c = self._gen_doc_c(org, project, team_size, contractors, departments,
                                 dep1_head, dep2_head, dep3_head, qa_lead, security_lead, fy)
        doc_d = self._gen_doc_d(org, project, milestones, fy, quarter, ga_date, pm_name)
        doc_e = self._gen_doc_e(org, project, fy, outdated_budget, budget_true, outdated_reason)
        doc_f = self._gen_doc_f(org, project, fy, lang, framework, tech_lead) if include_doc_f else None
        doc_g = self._gen_doc_g(org, project, fy, team_size, contractors, dep1_head) if include_doc_g else None

        # ── Build question bank (6-10 questions) ─────────────────────────────
        n_questions = rng.randint(6, 10)
        all_questions = self._build_questions(
            org, project, fy, quarter,
            budget_true, outdated_budget,
            arch_style, rpc_proto, orchestrator, db_engine,
            lang, framework, frontend, runtime,
            team_size, contractors, departments,
            dep1_head, dep2_head, dep3_head,
            lead_name, tech_lead, pm_name, qa_lead, security_lead,
            milestones, ga_date,
        )
        # Shuffle and take n_questions; always keep financial Q first (index 0)
        financial_q = all_questions[0]
        rest = all_questions[1:]
        rng.shuffle(rest)
        questions = [financial_q] + rest[:n_questions - 1]

        # ── Build corpus_files ────────────────────────────────────────────────
        corpus_files = {
            "doc_A.txt": doc_a,
            "doc_B.txt": doc_b,
            "doc_C.txt": doc_c,
            "doc_D.txt": doc_d,
            "doc_E.txt": doc_e,
        }
        if include_doc_f and doc_f:
            corpus_files["doc_F.txt"] = doc_f
        if include_doc_g and doc_g:
            corpus_files["doc_G.txt"] = doc_g

        doc_list = sorted(corpus_files.keys())

        # ── Workspace: blank answer template ──────────────────────────────────
        blank_answers = {
            "questions": [
                {"id": q["id"], "question": q["question"], "answer": ""}
                for q in questions
            ]
        }
        workspace_files = {
            "answer.json": json.dumps(blank_answers, indent=2) + "\n",
        }

        # ── Expected (grader-only) ────────────────────────────────────────────
        expected = {
            "domain": domain_cfg["id"],
            "org": org,
            "project": project,
            "fiscal_year": fy,
            "authority_hierarchy": domain_cfg["topics"],
            "outdated_doc": outdated_doc,
            "outdated_reason": outdated_reason,
            "true_budget": budget_true,
            "outdated_budget": outdated_budget,
            "questions": [
                {
                    "id": q["id"],
                    "question": q["question"],
                    "answer": q["answer"],
                    "answer_variants": q.get("answer_variants", [q["answer"]]),
                    "authoritative_doc": q["authoritative_doc"],
                    "topic": q["topic"],
                }
                for q in questions
            ],
            "doc_list": doc_list,
        }

        spec_md = self._generate_spec(
            org, project, label, fy, domain_cfg, questions, doc_list,
            outdated_doc, outdated_reason,
        )
        brief_md = self._generate_brief(org, project, label)

        return GeneratedTask(
            task_id=self.task_id,
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected=expected,
            workspace_files=workspace_files,
            corpus_files=corpus_files,
        )

    # ── Document generators ──────────────────────────────────────────────────

    def _gen_doc_a(self, org: str, project: str, fy: int, quarter: str,
                    budget: float, lead: str, pm: str) -> str:
        """doc_A: Authoritative for FINANCIAL data."""
        lines = [
            f"[1]  {org} — {project} Financial Summary (FY{fy})",
            f"[2]  Document type: Official Budget Report",
            f"[3]  Prepared by: Office of Finance",
            f"[4]",
            f"[5]  APPROVED BUDGET",
            f"[6]  Total approved budget for {project}: ${budget}M",
            f"[7]  Fiscal year: FY{fy}",
            f"[8]  Approval quarter: {quarter}",
            f"[9]  Approved by: Board of Directors",
            f"[10] Approval reference: BOD-FY{fy}-{quarter}-002",
            f"[11]",
            f"[12] BUDGET BREAKDOWN",
            f"[13] - Personnel costs:    {round(budget * 0.55, 2)}M",
            f"[14] - Infrastructure:     {round(budget * 0.20, 2)}M",
            f"[15] - Licensing & tools:  {round(budget * 0.10, 2)}M",
            f"[16] - Contingency (15%):  {round(budget * 0.15, 2)}M",
            f"[17]",
            f"[18] NOTES",
            f"[19] Project executive sponsor: {lead}",
            f"[20] Programme manager: {pm}",
            f"[21] This document supersedes all preliminary budget estimates.",
            f"[22] Any figures in draft or preliminary documents are NOT authoritative.",
        ]
        return "\n".join(lines) + "\n"

    def _gen_doc_b(self, org: str, project: str, arch_style: str, rpc_proto: str,
                    orchestrator: str, db_engine: str, lang: str, framework: str,
                    frontend: str, runtime: str, tech_lead: str) -> str:
        """doc_B: Authoritative for TECHNICAL SPECS."""
        lines = [
            f"[1]  {org} — {project} Technical Architecture Specification",
            f"[2]  Document type: Approved Technical Spec",
            f"[3]  Author: {tech_lead} (Technical Lead)",
            f"[4]",
            f"[5]  ARCHITECTURE OVERVIEW",
            f"[6]  Architecture style: {arch_style}",
            f"[7]  Inter-service communication: {rpc_proto}",
            f"[8]  Container orchestration: {orchestrator}",
            f"[9]  Primary datastore: {db_engine}",
            f"[10]",
            f"[11] TECHNOLOGY STACK",
            f"[12] - Backend language: {lang}",
            f"[13] - API framework: {framework}",
            f"[14] - Frontend framework: {frontend}",
            f"[15] - Runtime environment: {runtime}",
            f"[16]",
            f"[17] DESIGN DECISIONS",
            f"[18] The {arch_style} architecture was chosen after a formal RFC process.",
            f"[19] All inter-service calls use {rpc_proto} for type safety and performance.",
            f"[20] The {db_engine} datastore supports the required ACID guarantees.",
            f"[21] Technical lead responsible: {tech_lead}",
            f"[22] This specification is the single source of truth for technical decisions.",
        ]
        return "\n".join(lines) + "\n"

    def _gen_doc_c(self, org: str, project: str, team_size: int, contractors: int,
                    departments: list, dep1: str, dep2: str, dep3: str,
                    qa_lead: str, security_lead: str, fy: int) -> str:
        """doc_C: Authoritative for PERSONNEL."""
        total = team_size + contractors
        lines = [
            f"[1]  {org} — {project} Personnel & Staffing Record (FY{fy})",
            f"[2]  Document type: Official HR Register",
            f"[3]  Maintained by: Human Resources",
            f"[4]",
            f"[5]  HEADCOUNT SUMMARY",
            f"[6]  Full-time employees: {team_size}",
            f"[7]  Contractors: {contractors}",
            f"[8]  Total headcount: {total}",
            f"[9]",
            f"[10] TEAM STRUCTURE",
            f"[11] - {departments[0]} (head: {dep1}): core development",
            f"[12] - {departments[1]} (head: {dep2}): platform & reliability",
            f"[13] - {departments[2]} (head: {dep3}): quality & security",
            f"[14] - QA Lead: {qa_lead}",
            f"[15] - Security Lead: {security_lead}",
            f"[16]",
            f"[17] NOTES",
            f"[18] Headcount figures are as of the beginning of FY{fy}.",
            f"[19] Contractor count may vary throughout the fiscal year.",
            f"[20] This document is the authoritative source for all personnel data.",
        ]
        return "\n".join(lines) + "\n"

    def _gen_doc_d(self, org: str, project: str, milestones: list,
                    fy: int, quarter: str, ga_date: str, pm: str) -> str:
        """doc_D: Authoritative for TIMELINE / MILESTONES."""
        lines = [
            f"[1]  {org} — {project} Master Project Schedule (FY{fy})",
            f"[2]  Document type: Approved Project Timeline",
            f"[3]  Owner: {pm} (Programme Manager)",
            f"[4]",
            f"[5]  MILESTONE SCHEDULE",
        ]
        for i, (name, date) in enumerate(milestones, start=6):
            lines.append(f"[{i}]  - {name}: {date}")
        next_line = 6 + len(milestones)
        lines += [
            f"[{next_line}]",
            f"[{next_line+1}]  GENERAL AVAILABILITY",
            f"[{next_line+2}]  Target GA date: {ga_date}",
            f"[{next_line+3}]  Approval authority: {pm}",
            f"[{next_line+4}]",
            f"[{next_line+5}]  NOTES",
            f"[{next_line+6}]  Schedule approved in {quarter} FY{fy} planning session.",
            f"[{next_line+7}]  Any earlier dates in other documents are preliminary and superseded.",
            f"[{next_line+8}]  This document is the authoritative source for all timeline data.",
        ]
        return "\n".join(lines) + "\n"

    def _gen_doc_e(self, org: str, project: str, fy: int,
                    outdated_budget: float, true_budget: float,
                    reason: str) -> str:
        """doc_E: OUTDATED — must not be used for budget figures."""
        lines = [
            f"[1]  {org} — {project} Preliminary Cost Estimate",
            f"[2]  Document type: DRAFT — OUTDATED — DO NOT USE FOR BUDGET FIGURES",
            f"[3]  Status: SUPERSEDED",
            f"[4]",
            f"[5]  WARNING",
            f"[6]  This document contains a preliminary estimate only.",
            f"[7]  It has been superseded by the official Financial Summary (doc_A.txt).",
            f"[8]  Reason for supersession: {reason}",
            f"[9]",
            f"[10] PRELIMINARY ESTIMATE (OUTDATED)",
            f"[11] Estimated budget for {project}: ${outdated_budget}M",
            f"[12] Note: This figure is INCORRECT. The approved budget is ${true_budget}M.",
            f"[13]",
            f"[14] INSTRUCTION TO READERS",
            f"[15] Do NOT cite this document for financial data.",
            f"[16] Use doc_A.txt (Official Budget Report) for all budget figures.",
            f"[17] This document is retained for audit trail purposes only.",
        ]
        return "\n".join(lines) + "\n"

    def _gen_doc_f(self, org: str, project: str, fy: int,
                    lang: str, framework: str, tech_lead: str) -> str:
        """doc_F: Optional supplementary — tech onboarding guide (non-authoritative)."""
        lines = [
            f"[1]  {org} — {project} Developer Onboarding Guide (FY{fy})",
            f"[2]  Document type: Supplementary / Informational",
            f"[3]",
            f"[4]  GETTING STARTED",
            f"[5]  Primary language: {lang}",
            f"[6]  Framework: {framework}",
            f"[7]  For technical questions, contact: {tech_lead}",
            f"[8]",
            f"[9]  SETUP STEPS",
            f"[10] 1. Clone repository from internal git server",
            f"[11] 2. Run setup.sh to install dependencies",
            f"[12] 3. Configure environment variables per the README",
            f"[13] 4. Run test suite: make test",
            f"[14]",
            f"[15] NOTE: This is an informational document.",
            f"[16] For authoritative technical decisions see doc_B.txt.",
        ]
        return "\n".join(lines) + "\n"

    def _gen_doc_g(self, org: str, project: str, fy: int,
                    team_size: int, contractors: int, dep1_head: str) -> str:
        """doc_G: Optional supplementary — org chart snapshot (non-authoritative)."""
        total = team_size + contractors
        lines = [
            f"[1]  {org} — {project} Org Chart Snapshot (FY{fy})",
            f"[2]  Document type: Supplementary / Informational",
            f"[3]",
            f"[4]  ORG CHART SUMMARY",
            f"[5]  Programme Director: {dep1_head}",
            f"[6]  Approximate team size: {total} (including contractors)",
            f"[7]",
            f"[8]  NOTE: This org chart is a point-in-time snapshot.",
            f"[9]  For authoritative headcount data see doc_C.txt.",
        ]
        return "\n".join(lines) + "\n"

    # ── Question bank ────────────────────────────────────────────────────────

    def _build_questions(
        self, org, project, fy, quarter,
        budget_true, outdated_budget,
        arch_style, rpc_proto, orchestrator, db_engine,
        lang, framework, frontend, runtime,
        team_size, contractors, departments,
        dep1, dep2, dep3,
        lead_name, tech_lead, pm_name, qa_lead, security_lead,
        milestones, ga_date,
    ) -> list[dict]:
        """Build a pool of 12 questions covering all topics."""
        total_headcount = team_size + contractors
        budget_str = f"${budget_true}M"
        outdated_str = f"${outdated_budget}M"

        questions = [
            # ── FINANCIAL (authoritative: doc_A) ─────────────────────────────
            {
                "id": "Q1",
                "topic": "financial",
                "question": f"What is the approved total budget for the {project} project in FY{fy}?",
                "answer": budget_str,
                "answer_variants": [budget_str, f"{budget_true}M", f"${budget_true} million"],
                "authoritative_doc": "doc_A.txt",
            },
            {
                "id": "Q2",
                "topic": "financial",
                "question": f"Which document provides the authoritative approved budget for {project}?",
                "answer": "doc_A.txt",
                "answer_variants": ["doc_A.txt", "doc_A", "Official Budget Report"],
                "authoritative_doc": "doc_A.txt",
            },
            {
                "id": "Q3",
                "topic": "financial",
                "question": f"Why should doc_E.txt not be used for budget figures for {project}?",
                "answer": "It is outdated and has been superseded by the official Financial Summary in doc_A.txt.",
                "answer_variants": ["superseded", "outdated", "preliminary", "OUTDATED"],
                "authoritative_doc": "doc_E.txt",  # The doc itself explains this
            },
            # ── TECHNICAL (authoritative: doc_B) ─────────────────────────────
            {
                "id": "Q4",
                "topic": "technical",
                "question": f"What architecture style was chosen for the {project} project?",
                "answer": arch_style,
                "answer_variants": [arch_style],
                "authoritative_doc": "doc_B.txt",
            },
            {
                "id": "Q5",
                "topic": "technical",
                "question": f"What inter-service communication protocol does {project} use?",
                "answer": rpc_proto,
                "answer_variants": [rpc_proto],
                "authoritative_doc": "doc_B.txt",
            },
            {
                "id": "Q6",
                "topic": "technical",
                "question": f"What is the primary datastore for the {project} project?",
                "answer": db_engine,
                "answer_variants": [db_engine],
                "authoritative_doc": "doc_B.txt",
            },
            {
                "id": "Q7",
                "topic": "technical",
                "question": f"What backend language is used in the {project} technology stack?",
                "answer": lang,
                "answer_variants": [lang],
                "authoritative_doc": "doc_B.txt",
            },
            # ── PERSONNEL (authoritative: doc_C) ─────────────────────────────
            {
                "id": "Q8",
                "topic": "personnel",
                "question": f"How many full-time employees are on the {project} project in FY{fy}?",
                "answer": str(team_size),
                "answer_variants": [str(team_size)],
                "authoritative_doc": "doc_C.txt",
            },
            {
                "id": "Q9",
                "topic": "personnel",
                "question": f"What is the total headcount (FTEs plus contractors) for {project} in FY{fy}?",
                "answer": str(total_headcount),
                "answer_variants": [str(total_headcount)],
                "authoritative_doc": "doc_C.txt",
            },
            {
                "id": "Q10",
                "topic": "personnel",
                "question": f"Who is the QA Lead for the {project} project?",
                "answer": qa_lead,
                "answer_variants": [qa_lead],
                "authoritative_doc": "doc_C.txt",
            },
            # ── TIMELINE (authoritative: doc_D) ──────────────────────────────
            {
                "id": "Q11",
                "topic": "timeline",
                "question": f"What is the target General Availability date for the {project} project?",
                "answer": ga_date,
                "answer_variants": [ga_date],
                "authoritative_doc": "doc_D.txt",
            },
            {
                "id": "Q12",
                "topic": "timeline",
                "question": f"Who owns the master project schedule for {project}?",
                "answer": pm_name,
                "answer_variants": [pm_name],
                "authoritative_doc": "doc_D.txt",
            },
        ]
        return questions

    # ── Spec / Brief ──────────────────────────────────────────────────────────

    def _generate_spec(
        self, org: str, project: str, label: str, fy: int,
        domain_cfg: dict, questions: list[dict], doc_list: list[str],
        outdated_doc: str, outdated_reason: str,
    ) -> str:
        topics = domain_cfg["topics"]
        q_lines = "\n".join(
            f"{i+1}. [{q['id']}] {q['question']}"
            for i, q in enumerate(questions)
        )
        doc_lines = "\n".join(f"- `{d}`" for d in doc_list)
        authority_lines = "\n".join(
            f"- **{topic.upper()}** — authoritative source: `{doc}`"
            for topic, doc in topics.items()
        )
        return f"""# IR3: Multi-Source Cross-Reference QA

## Goal
Answer all questions using ONLY the provided offline corpus. No internet access.
Some documents contradict each other. You must use the authoritative source
for each topic as defined in the Document Authority Hierarchy below.

## Organisation
{org} — {label} (FY{fy}, Project: {project})

## Questions
{q_lines}

## Hard Requirements

1. Produce `answer.json` with answers to ALL questions:
   ```json
   {{
     "questions": [
       {{"id": "Q1", "question": "...", "answer": "<string>"}},
       ...
     ]
   }}
   ```
2. Each answer must come from the **authoritative document** for that topic.
3. Do **NOT** use `{outdated_doc}` for budget/financial figures — it is OUTDATED.
   Reason: {outdated_reason}
4. When documents disagree, the authority hierarchy below takes precedence.
5. Leave no answer field blank.

## Document Authority Hierarchy

{authority_lines}
- **OUTDATED (ignore for financial data)**: `{outdated_doc}` — {outdated_reason}

## Corpus
Located at `corpus/` (relative to workspace):
{doc_lines}

## Warning
Multiple documents contain overlapping or contradictory information.
Read the authority hierarchy carefully before answering.
Budget figures in `{outdated_doc}` are incorrect — always use `doc_A.txt` for financial data.
"""

    def _generate_brief(self, org: str, project: str, label: str) -> str:
        return f"""# IR3: Multi-Source Cross-Reference QA (Brief)

Read all documents in the corpus and answer the questions in `answer.json`.

Organisation: {org}
Subject: {label} — Project {project}

The corpus is in `corpus/` (relative to workspace).
Fill in each answer field in `answer.json`.
"""
