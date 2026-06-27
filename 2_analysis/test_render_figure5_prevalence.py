def test_prevalence_legend_is_single_readable_row():
    import importlib.util
    from pathlib import Path

    module_path = Path(__file__).resolve().parents[1] / "2_analysis" / "render_figure5_prevalence.py"
    spec = importlib.util.spec_from_file_location("render_figure5_prevalence", module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    assert getattr(mod, "LEGEND_NCOL", None) == 6
    assert getattr(mod, "LEGEND_FONT_SIZE", 0) >= 11
    assert getattr(mod, "LEGEND_BOTTOM_MARGIN", 0) >= 0.18
