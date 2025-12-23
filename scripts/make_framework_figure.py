from __future__ import annotations

from pathlib import Path


def main() -> None:
    # Generate a simple, ACL-friendly pipeline diagram as a PNG using matplotlib.
    # (Avoids external deps like graphviz in case they're not installed.)
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    repo_root = Path(__file__).resolve().parents[1]
    out_path = repo_root / "paper" / "figures" / "framework_pipeline.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 3.2))
    ax.set_axis_off()

    def box(x: float, y: float, w: float, h: float, text: str) -> FancyBboxPatch:
        p = FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.02,rounding_size=0.02",
            linewidth=1.5,
            edgecolor="#1f2937",
            facecolor="#eef2ff",
        )
        ax.add_patch(p)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=10)
        return p

    # Layout coordinates in [0,1] space
    y = 0.35
    h = 0.32
    w = 0.16
    gap = 0.03

    b1 = box(0.03, y, w, h, "Brief\n(JSON)")
    b2 = box(0.03 + (w + gap) * 1, y, w, h, "Orchestrator")
    b3 = box(0.03 + (w + gap) * 2, y, w, h, "Specialist Agents\n(alignment / table /\nconsistency / ...)")
    b4 = box(0.03 + (w + gap) * 3, y, w, h, "Quality Check\n(schema + guards)")
    b5 = box(0.03 + (w + gap) * 4, y, w, h, "Assembler")
    b6 = box(0.03 + (w + gap) * 5, y, w, h, "PRD Output\n(JSON)")

    def arrow(x1: float, y1: float, x2: float, y2: float) -> None:
        ax.annotate(
            "",
            xy=(x2, y2),
            xytext=(x1, y1),
            arrowprops=dict(arrowstyle="->", lw=1.6, color="#111827"),
        )

    # Arrows between boxes (center right -> center left)
    boxes = [b1, b2, b3, b4, b5, b6]
    for i in range(len(boxes) - 1):
        x1 = boxes[i].get_x() + boxes[i].get_width()
        y1 = boxes[i].get_y() + boxes[i].get_height() / 2
        x2 = boxes[i + 1].get_x()
        y2 = boxes[i + 1].get_y() + boxes[i + 1].get_height() / 2
        arrow(x1, y1, x2, y2)

    ax.text(
        0.5,
        0.08,
        "Ablations disable one agent; a No-Op placeholder preserves message flow so downstream stages always run.",
        ha="center",
        va="center",
        fontsize=9,
        color="#374151",
    )

    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[ok] wrote {out_path}")


if __name__ == "__main__":
    main()



