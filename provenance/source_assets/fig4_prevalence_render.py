"""Render fig4_v4: NON-signal-positive end-reason composition as a stacked bar.

Signal-positive ends carry no information when plotted per run: every run is
~95-99% signal-positive, so a "signal-positive" bar is always pinned at ~100%.
This figure therefore DROPS signal-positive and shows only the four
non-signal-positive end-reason classes, stacked, on a linear y-axis (% of run),
so the composition of the failure/eviction tail is directly readable.

For each hardware bucket the internal (Athey Lab) and external (public-archive)
cohorts are drawn side by side (solid vs dashed edge). The stacked segments are
mean class fractions across runs in the bucket; the thin cap is +1 SD on the
total non-signal-positive fraction across runs. An open marker at the axis floor
denotes a bucket measured with no non-signal-positive reads.
"""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter

HERE = Path(__file__).parent
data = json.load(open(HERE / 'fig4_v4_data.json'))

CLASSES = data['classes']
cls_color = {c['id']: c['color'] for c in CLASSES}
cls_label = {c['id']: c['label'] for c in CLASSES}

# Professional, print-friendly qualitative palette (Tableau 10 derived) chosen so
# the four non-signal-positive classes are clearly distinguishable, including the
# thin minority segments. Overrides the source colors.
PALETTE = {
    'umc':   '#A6CEE3',   # Unblock/mux change (bulky) -> LIGHT blue (low visual weight)
    'sn':    '#E15759',   # Signal negative         -> red
    'mc':    '#59A14F',   # Mux change              -> green
    'dsumc': '#B07AA1',   # Data-service unblock    -> purple
    'sp':    '#9C9C9C',   # Signal positive (unused; kept for completeness)
}
cls_color = {**cls_color, **PALETTE}

# Drop signal-positive (id 'sp'); stack the remaining four classes, largest
# typical-magnitude at the bottom for stable visual comparison across buckets.
STACK_IDS = [cid for cid in ('umc', 'sn', 'mc', 'dsumc') if cid in cls_color]

BAR_W = 0.34
GAP   = 0.07

CLASS_LABELS = {
    'signal_positive': 'Signal positive',
    'unblock_mux_change': 'Unblock/mux change',
    'data_service_unblock_mux': 'Data-service unblock/mux change',
    'mux_change': 'Mux change',
    'signal_negative': 'Signal negative',
}


def _h(n):
    """Compact read count: 24352149 -> '24.4M', 364669 -> '365k'."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}k"
    return str(n)


def _stack_total(bucket):
    """Mean total non-signal-positive % and the +1 SD on that total."""
    total = 0.0
    var = 0.0
    for cid in STACK_IDS:
        stat = bucket['cls'][cid]
        total += max(stat['mean'], 0.0)
        if stat['n'] > 1:
            var += stat['std'] ** 2
    return total, var ** 0.5


def draw_stack(ax, gx, bucket, edge_color, edge_style, lw, ymax):
    """Draw one stacked bar (non-signal-positive classes) centred at gx."""
    if bucket is None or bucket['n_runs'] == 0:
        ax.add_patch(Rectangle((gx - BAR_W / 2, 0), BAR_W, ymax,
                               facecolor='#f3f4f6', edgecolor='#d1d5db',
                               linestyle='--', lw=0.7, zorder=0))
        ax.text(gx, ymax * 0.5, 'n/a', ha='center', va='center',
                fontsize=8, color='#9ca3af')
        return
    bottom = 0.0
    for cid in STACK_IDS:
        v = max(bucket['cls'][cid]['mean'], 0.0)
        if v > 0:
            ax.add_patch(Rectangle((gx - BAR_W / 2, bottom), BAR_W, v,
                                   facecolor=cls_color[cid], edgecolor=edge_color,
                                   linewidth=lw * 0.7, linestyle=edge_style,
                                   alpha=0.95, zorder=3))
            bottom += v
    total, sd = _stack_total(bucket)
    if total <= 0:
        # measured zero: open marker just above the floor so the cell still reads
        ax.plot([gx], [ymax * 0.012], marker='o', ms=3.0, mfc='white',
                mec='#6b7280', mew=0.9, zorder=5)
        return
    # +1 SD on the total non-signal-positive fraction; clipped at the axis top
    # with an upward arrowhead when the (high-variance) whisker runs off-scale.
    if sd > 0:
        top = total + sd
        clipped = top > ymax * 0.985
        yHi = min(ymax * 0.985, top)
        ax.plot([gx, gx], [total, yHi], color='#0f172a', lw=0.8, alpha=0.7, zorder=4)
        if clipped:
            ax.plot([gx], [yHi], marker='^', ms=4.5, color='#0f172a', alpha=0.7, zorder=4)
        else:
            cap = BAR_W * 0.22
            ax.plot([gx - cap, gx + cap], [yHi, yHi], color='#0f172a', lw=0.8,
                    alpha=0.7, zorder=4)
    # total label on top of the stack
    ax.text(gx, total + ymax * 0.015, f'{total:.1f}%', ha='center', va='bottom',
            fontsize=7.4, color='#0f172a', fontweight='600', zorder=6)


def draw_panel(ax, panel, title, ymax):
    buckets = panel['buckets']
    N = len(buckets)
    INT = panel['internal']
    EXT = panel['external']
    x_int, x_ext = [], []
    for i in range(N):
        x_int.append(i - (BAR_W / 2 + GAP / 2))
        x_ext.append(i + (BAR_W / 2 + GAP / 2))
    for i, b in enumerate(buckets):
        draw_stack(ax, x_int[i], INT.get(b), '#0f172a', '-', 1.1, ymax)
        draw_stack(ax, x_ext[i], EXT.get(b), '#b45309', '--', 1.3, ymax)

    ax.set_xlim(-0.7, N - 0.3)
    ax.set_ylim(0, ymax)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'{y:g}%'))
    ax.tick_params(axis='y', labelsize=9)
    ax.grid(axis='y', which='major', color='#e5e7eb', lw=0.6, zorder=0)
    ax.set_axisbelow(True)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_xticks(range(N))
    ax.set_xticklabels(buckets, rotation=0, fontsize=10, fontweight='600')
    ax.tick_params(axis='x', length=0, pad=6)
    ax.set_title(title, fontsize=13, fontweight='700', loc='left', pad=10)

    # Int/Ext + run-count strip below the axis (axes-fraction y).
    trans = ax.get_xaxis_transform()
    y_src, y_n = -0.075, -0.115
    for i, b in enumerate(buckets):
        iB = INT.get(b)
        eB = EXT.get(b)
        ax.text(x_int[i], y_src, 'Int', transform=trans, ha='center', va='top',
                fontsize=8.5, color='#334155', family='monospace', fontweight='bold')
        ax.text(x_ext[i], y_src, 'Ext', transform=trans, ha='center', va='top',
                fontsize=8.5, color='#334155', family='monospace', fontweight='bold')
        ax.text(x_int[i], y_n,
                f"n={iB['n_runs']}·{_h(iB['n_reads'])}" if iB and iB['n_runs'] else 'n/a',
                transform=trans, ha='center', va='top', fontsize=6.6, color='#64748b',
                family='monospace')
        ax.text(x_ext[i], y_n,
                f"n={eB['n_runs']}·{_h(eB['n_reads'])}" if eB and eB['n_runs'] else 'n/a',
                transform=trans, ha='center', va='top', fontsize=6.6, color='#64748b',
                family='monospace')


# Global y-max across both panels so the two share a comparable linear scale.
def _panel_ymax(panel):
    m = 0.0
    for src in ('internal', 'external'):
        for b in panel['buckets']:
            bucket = panel[src].get(b)
            if bucket and bucket['n_runs']:
                total, _ = _stack_total(bucket)
                m = max(m, total)
    return m

# Scale the axis to the stack TOTALS (not the high-variance +1 SD whiskers) so the
# bars fill the panel and the minority segments stay legible; the rare whisker that
# overshoots is clipped with an arrowhead (see draw_stack).
ymax = max(_panel_ymax(data['panels']['flowcell']),
           _panel_ymax(data['panels']['kit'])) * 1.32
ymax = max(ymax, 1.0)

fig, axes = plt.subplots(1, 2, figsize=(15, 6.4), gridspec_kw={'width_ratios': [1.05, 1.0]})
draw_panel(axes[0], data['panels']['flowcell'], 'A. Grouped by flow-cell type', ymax)
draw_panel(axes[1], data['panels']['kit'], 'B. Grouped by sequencing-kit family', ymax)

for ax in axes:
    ax.set_ylabel('Non-signal-positive reads (% of run)', fontsize=11)

# Legend: the four stacked (non-signal-positive) classes, then the Int/Ext edge
# convention. Signal-positive is intentionally omitted (always ~100%).
handles = [mpatches.Patch(facecolor=cls_color[cid], edgecolor='#0f172a', lw=0.4,
                          label=CLASS_LABELS.get(cls_label[cid], cls_label[cid]))
           for cid in STACK_IDS]
handles.append(mpatches.Patch(facecolor='white', edgecolor='#0f172a', lw=1.2,
                              label='Internal (Athey Lab) — solid edge'))
handles.append(mpatches.Patch(facecolor='white', edgecolor='#b45309', lw=1.4,
                              linestyle='--', label='External (public archives) — dashed edge'))
fig.legend(handles=handles, loc='lower center', ncol=3, frameon=False,
           fontsize=10, bbox_to_anchor=(0.5, 0.005))

fig.suptitle('Non-signal-positive end-reason composition by hardware',
             fontsize=15.5, fontweight='700', y=0.985)

plt.tight_layout(rect=[0.01, 0.12, 1, 0.94])

OUT_PDF = HERE / 'fig4_v4.pdf'
OUT_PNG = HERE / 'fig4_v4.png'
fig.savefig(OUT_PDF, bbox_inches='tight')
fig.savefig(OUT_PNG, bbox_inches='tight', dpi=300)
print(f"wrote {OUT_PDF} ({OUT_PDF.stat().st_size:,} bytes)")
print(f"wrote {OUT_PNG} ({OUT_PNG.stat().st_size:,} bytes)")
