# A-Unit

**No Gods. No Masters. Just Agents.**

A portable squad for production software engineering: focused specialists, a coordinating main session, and evidence-based validation.

**Status: agent-contract draft.** Role definitions are available for review. Runtime adapters, installation, and runtime validation are not yet implemented.

## The gang

| Agent | Specialty | Definition |
| --- | --- | --- |
| Hannibal | Main-session commander | [hannibal](agents/hannibal.md) |
| Plan Solo | System design | [plan-solo](agents/plan-solo.md) |
| B.A. Barac++ | Backend C++ | [baracus](agents/baracus.md) |
| Go-rilla | Backend Go | [go-rilla](agents/go-rilla.md) |
| Snake Eyes | Backend Python | [snake-eyes](agents/snake-eyes.md) |
| The Nodefather | Backend Node.js / JavaScript | [nodefather](agents/nodefather.md) |
| Sharp Shooter | Backend .NET / C# | [sharp-shooter](agents/sharp-shooter.md) |
| Face | Frontend React / JavaScript | [face](agents/face.md) |
| Droid Rage | Android | [droid-rage](agents/droid-rage.md) |
| Swift Justice | iOS | [swift-justice](agents/swift-justice.md) |
| Murdock | QA and testing | [murdock](agents/murdock.md) |
| Pit Crew | Integration and runtime | [pit-crew](agents/pit-crew.md) |

## Working with the squad

Hannibal coordinates the main session and selects specialists according to the task. Small changes can be completed directly; independent work can be delegated with clear scope, interfaces, and edit ownership.

Each role follows the [shared engineering contract](agents/_shared/engineering-contract.md). Packaging must include the complete contract before each role's own instructions; Hannibal's definition already includes the coordination procedure. Source links are for browsing, not runtime imports. Installed agents must not need the source checkout to load these instructions. Task ownership is supplied in the assignment.

Target repositories own their conventions, commands, and requirements through their applicable instructions. The optional [project instruction template](templates/AGENTS.md) provides a starting point.

Codex CLI is the first runtime target. Model selection inherits from the active session. Role instructions describe behavior; runtime permissions remain the harness's responsibility. Display names are provisional codenames.

## License

[Apache License 2.0](LICENSE).
