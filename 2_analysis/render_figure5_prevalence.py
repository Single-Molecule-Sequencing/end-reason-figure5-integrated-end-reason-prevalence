import csv
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / '1_experiment' / 'tables' / 'fig4_run_level_summary.csv'
OUT_DIR = ROOT / '3_results' / 'figures'
OUT_DIR.mkdir(parents=True, exist_ok=True)

PALETTE = {
    'umc': '#A6CEE3',
    'sn': '#E15759',
    'mc': '#59A14F',
    'dsumc': '#B07AA1',
    'sp': '#9C9C9C',
}
STACK_IDS = ['umc', 'sn', 'mc', 'dsumc']
BAR_W = 0.34
GAP = 0.07

CLASS_LABELS = {
    'umc': 'Unblock/mux change',
    'dsumc': 'Data-service unblock/mux change',
    'mc': 'Mux change',
    'sn': 'Signal negative',
}

FLOW_BUCKETS = ['FLO-MIN114', 'FLO-FLG114', 'FLO-PRO114M', 'FLO-MIN106', 'FLO-PRO111']
KIT_BUCKETS = ['LSK114', 'RBK114', 'LSK109', 'RBK004']


def _f(v):
    try:
        return float(v)
    except Exception:
        return 0.0


def _i(v):
    try:
        return int(float(v))
    except Exception:
        return 0


def _h(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}k"
    return str(n)


def bucketize(rows, bucket_field, bucket_order):
    grouped = defaultdict(list)
    for r in rows:
        grouped[r.get(bucket_field, '').strip()].append(r)

    out = {}
    for b in bucket_order:
        rs = grouped.get(b, [])
        if not rs:
            out[b] = None
            continue

        cls_vals = {cid: [] for cid in STACK_IDS}
        n_reads = 0
        for r in rs:
            n_reads += _i(r.get('called_reads', '0'))
            cls_vals['umc'].append(_f(r.get('unblock_mux_change_pct', '0')))
            cls_vals['sn'].append(_f(r.get('signal_negative_pct', '0')))
            cls_vals['mc'].append(_f(r.get('mux_change_pct', '0')))
            cls_vals['dsumc'].append(_f(r.get('data_service_unblock_mux_change_pct', '0')))

        cls_stats = {}
        for cid, vals in cls_vals.items():
            mean = sum(vals) / len(vals)
            if len(vals) > 1:
                var = sum((v - mean) ** 2 for v in vals) / (len(vals) - 1)
                std = var ** 0.5
            else:
                std = 0.0
            cls_stats[cid] = {'mean': mean, 'std': std, 'n': len(vals)}

        out[b] = {'n_runs': len(rs), 'n_reads': n_reads, 'cls': cls_stats}
    return out


def _stack_total(bucket):
    total = 0.0
    var = 0.0
    for cid in STACK_IDS:
        stat = bucket['cls'][cid]
        total += max(stat['mean'], 0.0)
        if stat['n'] > 1:
            var += stat['std'] ** 2
    return total, var ** 0.5


def draw_stack(ax, gx, bucket, edge_color, edge_style, lw, ymax):
    if bucket is None or bucket['n_runs'] == 0:
        ax.add_patch(Rectangle((gx - BAR_W / 2, 0), BAR_W, ymax,
                               facecolor='#f3f4f6', edgecolor='#d1d5db',
                               linestyle='--', lw=0.7, zorder=0))
        ax.text(gx, ymax * 0.5, 'n/a', ha='center', va='center', fontsize=8, color='#9ca3af')
        return

    bottom = 0.0
    for cid in STACK_IDS:
        v = max(bucket['cls'][cid]['mean'], 0.0)
        if v > 0:
            ax.add_patch(Rectangle((gx - BAR_W / 2, bottom), BAR_W, v,
                                   facecolor=PALETTE[cid], edgecolor=edge_color,
                                   linewidth=lw * 0.7, linestyle=edge_style,
                                   alpha=0.95, zorder=3))
            bottom += v

    total, sd = _stack_total(bucket)
    if total <= 0:
        ax.plot([gx], [ymax * 0.012], marker='o', ms=3.0, mfc='white', mec='#6b7280', mew=0.9, zorder=5)
        return

    if sd > 0:
        top = total + sd
        clipped = top > ymax * 0.985
        y_hi = min(ymax * 0.985, top)
        ax.plot([gx, gx], [total, y_hi], color='#0f172a', lw=0.8, alpha=0.7, zorder=4)
        if clipped:
            ax.plot([gx], [y_hi], marker='^', ms=4.5, color='#0f172a', alpha=0.7, zorder=4)
        else:
            cap = BAR_W * 0.22
            ax.plot([gx - cap, gx + cap], [y_hi, y_hi], color='#0f172a', lw=0.8, alpha=0.7, zorder=4)

    ax.text(gx, total + ymax * 0.015, f'{total:.1f}%', ha='center', va='bottom',
            fontsize=7.4, color='#0f172a', fontweight='600', zorder=6)


def draw_panel(ax, panel, title, ymax):
    buckets = panel['buckets']
    n = len(buckets)
    i_map = panel['internal']
    e_map = panel['external']

    x_int, x_ext = [], []
    for i in range(n):
        x_int.append(i - (BAR_W / 2 + GAP / 2))
        x_ext.append(i + (BAR_W / 2 + GAP / 2))

    for i, b in enumerate(buckets):
        draw_stack(ax, x_int[i], i_map.get(b), '#0f172a', '-', 1.1, ymax)
        draw_stack(ax, x_ext[i], e_map.get(b), '#b45309', '--', 1.3, ymax)

    ax.set_xlim(-0.7, n - 0.3)
    ax.set_ylim(0, ymax)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'{y:g}%'))
    ax.tick_params(axis='y', labelsize=9)
    ax.grid(axis='y', which='major', color='#e5e7eb', lw=0.6, zorder=0)
    ax.set_axisbelow(True)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_xticks(range(n))
    ax.set_xticklabels(buckets, rotation=0, fontsize=10, fontweight='600')
    ax.tick_params(axis='x', length=0, pad=6)
    ax.set_title(title, fontsize=13, fontweight='700', loc='left', pad=10)

    trans = ax.get_xaxis_transform()
    y_src, y_n = -0.075, -0.115
    for i, b in enumerate(buckets):
        i_b = i_map.get(b)
        e_b = e_map.get(b)
        ax.text(x_int[i], y_src, 'Int', transform=trans, ha='center', va='top',
                fontsize=8.5, color='#334155', family='monospace', fontweight='bold')
        ax.text(x_ext[i], y_src, 'Ext', transform=trans, ha='center', va='top',
                fontsize=8.5, color='#334155', family='monospace', fontweight='bold')
        ax.text(x_int[i], y_n,
                f"n={i_b['n_runs']}·{_h(i_b['n_reads'])}" if i_b and i_b['n_runs'] else 'n/a',
                transform=trans, ha='center', va='top', fontsize=6.6, color='#64748b', family='monospace')
        ax.text(x_ext[i], y_n,
                f"n={e_b['n_runs']}·{_h(e_b['n_reads'])}" if e_b and e_b['n_runs'] else 'n/a',
                transform=trans, ha='center', va='top', fontsize=6.6, color='#64748b', family='monospace')


def _panel_ymax(panel):
    m = 0.0
    for src in ('internal', 'external'):
        for b in panel['buckets']:
            bucket = panel[src].get(b)
            if bucket and bucket['n_runs']:
                total, _ = _stack_total(bucket)
                m = max(m, total)
    return m


def main():
    with TABLE.open(newline='') as fh:
        rows = list(csv.DictReader(fh))

    internal = [r for r in rows if r.get('catalog_match_status', '').strip().lower() != 'matched']
    external = [r for r in rows if r.get('catalog_match_status', '').strip().lower() == 'matched']

    data = {
        'panels': {
            'flowcell': {
                'buckets': FLOW_BUCKETS,
                'internal': bucketize(internal, 'flow_cell_product_code', FLOW_BUCKETS),
                'external': bucketize(external, 'flow_cell_product_code', FLOW_BUCKETS),
            },
            'kit': {
                'buckets': KIT_BUCKETS,
                'internal': bucketize(internal, 'sequencing_kit', KIT_BUCKETS),
                'external': bucketize(external, 'sequencing_kit', KIT_BUCKETS),
            },
        }
    }

    ymax = max(_panel_ymax(data['panels']['flowcell']), _panel_ymax(data['panels']['kit'])) * 1.32
    ymax = max(ymax, 1.0)

    fig, axes = plt.subplots(1, 2, figsize=(15, 6.4), gridspec_kw={'width_ratios': [1.05, 1.0]})
    draw_panel(axes[0], data['panels']['flowcell'], 'A. Grouped by flow-cell type', ymax)
    draw_panel(axes[1], data['panels']['kit'], 'B. Grouped by sequencing-kit family', ymax)

    for ax in axes:
        ax.set_ylabel('Non-signal-positive reads (% of run)', fontsize=11)

    handles = [
        mpatches.Patch(facecolor=PALETTE[cid], edgecolor='#0f172a', lw=0.4, label=CLASS_LABELS[cid])
        for cid in STACK_IDS
    ]
    handles.append(mpatches.Patch(facecolor='white', edgecolor='#0f172a', lw=1.2,
                                  label='Internal (Athey Lab) — solid edge'))
    handles.append(mpatches.Patch(facecolor='white', edgecolor='#b45309', lw=1.4, linestyle='--',
                                  label='External (public archives) — dashed edge'))
    fig.legend(handles=handles, loc='lower center', ncol=3, frameon=False, fontsize=10,
               bbox_to_anchor=(0.5, 0.005))

    fig.suptitle('Non-signal-positive end-reason composition by hardware',
                 fontsize=15.5, fontweight='700', y=0.985)
    plt.tight_layout(rect=[0.01, 0.12, 1, 0.94])

    out_pdf = OUT_DIR / 'figure5_integrated_end_reason_prevalence.pdf'
    out_png = OUT_DIR / 'figure5_integrated_end_reason_prevalence.png'
    fig.savefig(out_pdf, bbox_inches='tight')
    fig.savefig(out_png, bbox_inches='tight', dpi=300)
    print(f'wrote {out_pdf} ({out_pdf.stat().st_size:,} bytes)')
    print(f'wrote {out_png} ({out_png.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
