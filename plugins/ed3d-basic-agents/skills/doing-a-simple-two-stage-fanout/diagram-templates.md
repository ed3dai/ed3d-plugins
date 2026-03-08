# Diagram Templates for Fan-Out Analysis

Templates for visualizing the Worker → Critic → Summarizer pipeline. Generate one diagram per plan using the parameters you computed.

## Mermaid Template

Use Mermaid when the plan is written to a markdown file (most cases). Adapt the node counts to match your computed layout.

```mermaid
graph TD
    subgraph planning["PLANNING"]
        P["Planner"]
    end

    subgraph workers["WORKERS"]
        W01["W01<br/>S01-S03"]
        W02["W02<br/>S04-S06"]
        W03["W03<br/>S07-S09"]
    end

    subgraph critics["CRITICS"]
        C01["C01"]
        C02["C02"]
    end

    subgraph summary["SUMMARIZER"]
        S["Summarizer"]
    end

    P --> W01
    P --> W02
    P --> W03

    W01 --> C01
    W02 --> C01
    W02 --> C02
    W03 --> C02

    C01 --> S
    C02 --> S

    classDef planner fill:#4A90E2,stroke:#2E5C8A,stroke-width:2px,color:#fff
    classDef worker fill:#50C878,stroke:#2D7A47,stroke-width:2px,color:#fff
    classDef critic fill:#F5A623,stroke:#C17A1A,stroke-width:2px,color:#fff
    classDef summarizer fill:#9B59B6,stroke:#6C3A7C,stroke-width:2px,color:#fff

    class P planner
    class W01,W02,W03 worker
    class C01,C02 critic
    class S summarizer
```

### Mermaid Syntax Notes

- **Node labels**: Use `"W01<br/>S01-S03"` to show which segments each worker handles. `<br/>` creates a line break inside the node.
- **Subgraphs**: Wrap each stage in `subgraph id["DISPLAY NAME"] ... end`. The quoted display name supports spaces and caps.
- **Styling**: Define styles with `classDef` and apply with `class node1,node2 styleName`. Place style definitions at the end.
- **Edges**: Write each edge explicitly (`P --> W01`). Mermaid does not reliably support `P --> {W01, W02}` shorthand.
- **Scaling**: For large layouts (>10 workers), consider collapsing into a summary node like `W01_10["W01-W10<br/>30 segments"]` to keep the diagram readable.

### Mermaid Gotchas

1. Node IDs are case-sensitive. `W01` and `w01` are different nodes.
2. Subgraph node association: a node belongs to the first subgraph it appears in. Declare nodes inside their subgraph.
3. Special characters in labels need double quotes: `A["Label with --> arrow"]`.
4. Long diagrams render poorly. Cap at ~15 visible nodes. Collapse ranges for larger layouts.


## Graphviz (DOT) Template

Use Graphviz when the user requests it, or when you need publication-quality output. Graphviz produces cleaner layouts for large graphs.

```dot
digraph FanOutAnalysis {
    rankdir=TB;
    node [fontname="Arial", fontsize=11, shape=box, style=filled];
    edge [color="#666666"];

    subgraph cluster_planning {
        label="Planning";
        style=filled;
        fillcolor="#E8F0FF";
        color="#2E5C8A";
        P [label="Planner", fillcolor="#4A90E2", fontcolor=white];
    }

    subgraph cluster_workers {
        label="Workers";
        style=filled;
        fillcolor="#E8FFE8";
        color="#2D7A47";
        W01 [label="W01\nS01-S03", fillcolor="#50C878", fontcolor=white];
        W02 [label="W02\nS04-S06", fillcolor="#50C878", fontcolor=white];
        W03 [label="W03\nS07-S09", fillcolor="#50C878", fontcolor=white];
    }

    subgraph cluster_critics {
        label="Critics";
        style=filled;
        fillcolor="#FFF4E8";
        color="#C17A1A";
        C01 [label="C01", fillcolor="#F5A623", fontcolor=white];
        C02 [label="C02", fillcolor="#F5A623", fontcolor=white];
    }

    subgraph cluster_summarizer {
        label="Summarizer";
        style=filled;
        fillcolor="#F5E8FF";
        color="#6C3A7C";
        S [label="Summarizer", fillcolor="#9B59B6", fontcolor=white];
    }

    P -> {W01; W02; W03};

    W01 -> C01;
    W02 -> C01;
    W02 -> C02;
    W03 -> C02;

    {C01; C02} -> S;
}
```

### Graphviz Syntax Notes

- **Fan-out shorthand**: `P -> {W01; W02; W03};` creates edges from P to all three nodes. Use semicolons inside braces, not commas.
- **Fan-in shorthand**: `{C01; C02} -> S;` creates edges from both critics to the summarizer.
- **Clusters**: Only subgraphs named `cluster_*` draw bounding boxes. Regular `subgraph` is structural only.
- **Line breaks in labels**: Use `\n` (not `<br/>`).
- **Rendering**: `dot -Tpng graph.dot -o graph.png` or `dot -Tsvg graph.dot -o graph.svg`.

### Graphviz Gotchas

1. Every statement needs a semicolon terminator.
2. The `cluster_` prefix is required for visual bounding boxes.
3. `rankdir=TB` affects the entire graph — you cannot mix vertical and horizontal sections.
4. Edge shorthand `{A; B} -> {C; D}` creates the full cross product (4 edges). Be explicit if you want specific pairings.

## When to Use Which

| Criterion | Mermaid | Graphviz |
|-----------|---------|----------|
| Output target | Markdown files, GitHub PRs | Rendered images, publications |
| Large graphs (>15 nodes) | Collapse to ranges | Handles natively |
| User familiarity | More common | Less common |
| Layout control | Limited | Fine-grained |
| Default choice | **Yes** | Only if requested |
