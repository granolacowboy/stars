# ★ granolacowboy's research library

[![Verified](https://github.com/granolacowboy/granolacowboy.dev/actions/workflows/verify-stars.yml/badge.svg)](https://github.com/granolacowboy/granolacowboy.dev/actions/workflows/verify-stars.yml)

A curated snapshot of **2,171 list memberships** across **28 public GitHub Lists**. The same repository may appear in more than one list, so this is intentionally described as membership count rather than a unique-repository count.

**Snapshot:** `2026-09-20` UTC · Generated from manually curated GitHub Lists by [`scripts/generate.py`](scripts/generate.py).

## How to read this

This is a working research library, not a recommendation engine or ranking.

- **Selection is manual.** I decide which repositories belong in each GitHub List.
- **Rendering is deterministic.** The generator turns those Lists into browsable Markdown snapshots; refreshes are explicit so an unattended failure cannot silently rewrite the library.
- **Ordering is mechanical.** Entries are sorted by GitHub star count for scanability; stars are not treated as a quality score.
- **Metadata is point-in-time.** Descriptions, languages, star counts, and archive state can change after the snapshot.
- **Overlap is expected.** A repository can belong to multiple lists.
- **Inclusion is not endorsement.** Lists include tools I am evaluating, comparing, monitoring, or may want to revisit.

Maintained by [Rich Berman](https://github.com/granolacowboy) / [MHSB Solutions](https://github.com/MHSBai) · [granolacowboy.dev](https://granolacowboy.dev)

## Verification and refresh

The central portfolio verifier compiles the generator and runs its offline unit tests against `main`. To refresh the research snapshot itself, authenticate the GitHub CLI as the account whose Lists should be rendered and run:

```bash
python scripts/generate.py
```

The generator fetches all public Lists before writing, retries transient GraphQL failures, and fails closed if the source data is empty or unavailable. Generated Markdown, research views, and the rolling star-count snapshot are then committed together.

## Browse by topic

| List | Count | About |
|---|--:|---|
| [AI/ML Frameworks](lists/ai-ml-frameworks.md) | 100 | ML/DL training & inference frameworks, model libraries, model routing, and knowledge graphs |
| [LLM Apps & RAG](lists/llm-apps-rag.md) | 100 | LLM applications, RAG pipelines, chatbots, and prompt engineering |
| [Awesome Lists & Resources](lists/awesome-lists-resources.md) | 100 | Curated lists, learning resources, and collections |
| [Security](lists/security.md) | 100 | Security tooling, secrets management, pentest/red-team, and vulnerability research |
| [AI Agents & Orchestration](lists/ai-agents-orchestration.md) | 100 | Multi-agent systems, swarm frameworks, agent coordination, and orchestration tools |
| [Media & Content](lists/media-content.md) | 100 | Media players, streaming, video/photo management, and content tools |
| [Web Scraping & Automation](lists/web-scraping-automation.md) | 100 | Web scraping, crawlers, and browser automation |
| [Web & Frontend](lists/web-frontend.md) | 100 | React, Next.js, CSS frameworks, and frontend development |
| [DevOps & Infrastructure](lists/devops-infrastructure.md) | 100 | Docker, Kubernetes, CI/CD, cloud, and infrastructure tools |
| [Coding Tools & AI IDEs](lists/coding-tools-ai-ides.md) | 100 | Claude Code extensions, AI coding assistants, vibe coding platforms, and developer tools |
| [Mobile & Desktop Apps](lists/mobile-desktop-apps.md) | 100 | iOS, Android, cross-platform mobile and desktop applications |
| [Backend & APIs](lists/backend-apis.md) | 100 | Backend frameworks, REST/GraphQL APIs, and server development |
| [Terminal & CLI Tools](lists/terminal-cli-tools.md) | 100 | Terminal utilities, file managers, shell tools, and CLI applications |
| [Self-Hosted & Privacy](lists/self-hosted-privacy.md) | 100 | Self-hosted alternatives, privacy tools, and decentralized apps |
| [Knowledge Mgmt & Notes](lists/knowledge-mgmt-notes.md) | 100 | Note-taking, wikis, knowledge bases, and personal knowledge management |
| [Productivity & Project Mgmt](lists/productivity-project-mgmt.md) | 100 | Productivity tools, project management, and workflow apps |
| [Networking & VPN](lists/networking-vpn.md) | 96 | VPN, proxy, network monitoring, and connectivity tools |
| [Browser Extensions](lists/browser-extensions.md) | 66 | Chrome, Firefox, and Safari browser extensions |
| [MCP Servers & Integrations](lists/mcp-servers-integrations.md) | 64 | Model Context Protocol servers, tools, and integrations |
| [Home Automation & IoT](lists/home-automation-iot.md) | 64 | Smart home, home automation, and IoT projects |
| [Finance & Trading](lists/finance-trading.md) | 53 | Trading bots, fintech, cryptocurrency, and financial analysis |
| [Bots & Messaging](lists/bots-messaging.md) | 52 | Chat bots, Telegram bots, Discord bots, and messaging platforms |
| [OSINT & Forensics](lists/osint-forensics.md) | 45 | Open source intelligence, digital forensics, and investigation tools |
| [Git & Version Control](lists/git-version-control.md) | 42 | Git tools, GitHub utilities, and version control enhancements |
| [Remote Work & Jobs](lists/remote-work-jobs.md) | 28 | Remote work resources, job boards, and freelancing tools |
| [Voice & Conversational AI](lists/voice-conversational-ai.md) | 26 | Voice agents, speech AI, and multimodal conversational frameworks |
| [Gaming](lists/gaming.md) | 18 | Game development, game engines, emulators, and gaming tools |
| [WebRTC & Real-time](lists/webrtc-real-time.md) | 17 | WebRTC, SFU, video conferencing, and real-time communication |

<sub>Snapshot 2026-09-20 UTC · 2,171 list memberships · 28 lists. The generator will report unique-repository count on the next regeneration.</sub>
