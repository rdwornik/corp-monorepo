# Architecture Diagrams

3 diagrams per Council Decision #25. Open `.svg` files directly in VS Code to view.

| Diagram | View | Edit | What it shows |
|---------|------|------|--------------|
| System context | system-context.svg | system-context.mermaid | External boundaries: Rob, APIs, Vault, MyWork |
| Module map | container-module.svg | container-module.mermaid | 12 modules + 3 databases + dependency layers |
| Magistrala | magistrala-pipeline.svg | magistrala-pipeline.mermaid | File → vault pipeline (9 steps) |

## Rules
- Open `.svg` to VIEW diagrams
- Edit `.mermaid` files only — never hand-edit .svg
- After editing: `powershell scripts/render-diagrams.ps1`
- Requires: `npm install -g @mermaid-js/mermaid-cli`
