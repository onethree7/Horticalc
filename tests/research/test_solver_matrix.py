from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest
import yaml

import scripts.solver_matrix as solver_matrix
from horticalc.data_io import load_fertilizers

pytestmark = pytest.mark.research


def _cases() -> dict:
    return yaml.safe_load(solver_matrix.DEFAULT_CASES_PATH.read_text(encoding="utf-8"))


def test_resolve_allowed_fertilizers_rejects_whitespace_with_hint() -> None:
    fertilizers = {
        "Compo Fetrilon Combi 1": object(),
        "Yara Tera CALCINIT": object(),
    }

    with pytest.raises(ValueError) as exc_info:
        solver_matrix.resolve_allowed_fertilizers(
            ["Compo Fetrilon Combi 1 ", "Yara Tera CALCINIT"],
            fertilizers,
        )

    message = str(exc_info.value)
    assert "without surrounding whitespace" in message
    assert "'Compo Fetrilon Combi 1'" in message


def test_score_solution_follows_solver_objective_elements_and_scores_s() -> None:
    targets = {"K": 0.0, "Fe": 1.0, "S": 100.0, "HCO3": 0.0}
    achieved = {"K": 2.0, "Fe": 1.1, "S": 150.0, "HCO3": 100.0}

    score = solver_matrix.score_solution(targets, achieved, objective_elements=["Fe", "S"])

    assert score["elements"]["K"]["category"] == "ignored"
    assert score["elements"]["S"]["category"] == "macro"
    assert score["elements"]["S"]["score"] == 50.0
    assert score["elements"]["HCO3"]["category"] == "ignored"


def test_score_solution_scores_zero_objective_target() -> None:
    score = solver_matrix.score_solution({"K": 0.0}, {"K": 2.0}, objective_elements=["K"])

    assert score["elements"]["K"]["error_percent"] is None
    assert score["elements"]["K"]["score"] == 100.0
    assert score["composite_score"] == 300.0


def test_canonical_config_catalog_covers_requested_settings() -> None:
    configs = solver_matrix.solver_config_cases(_cases(), "matrix")

    assert len(configs) == 135
    assert configs[0].experiment_id == "baseline"
    assert all(config.values["nitrogen_objective_mode"] == "n_total_only" for config in configs)
    assert all(config.values["s_objective_enabled"] is True for config in configs)
    assert any(config.values["singleton_max_regress_pp"] == 10.0 for config in configs)
    assert any(config.values["singleton_underfill_share_threshold"] == 0.0 for config in configs)
    assert any(config.values["singleton_supplier_enabled"] is True for config in configs)
    assert any(config.values["singleton_supplier_enabled"] is False for config in configs)
    assert any(config.values["singleton_underfill_enabled"] is True for config in configs)
    assert any(config.values["singleton_underfill_enabled"] is False for config in configs)
    assert {config.values["irls_max_outer_iter"] for config in configs} >= {1, 2, 4, 8, 12}
    assert all(config.values["irls_max_outer_iter"] >= 1 for config in configs)
    assert all(config.values["singleton_underfill_max_iter"] >= 1 for config in configs)
    assert {config.values["scale_eps_mg_per_l"] for config in configs} >= {0.1, 0.5, 1.0, 2.0, 5.0}
    assert {config.values["overshoot_penalty"] for config in configs} >= {0.0, 0.25, 1.0, 1.5, 3.0, 10.0}
    assert sum(config.experiment_id == "confirmation_best" for config in configs) == 7


def test_benchmark_corpus_and_recipe_union_are_explicit() -> None:
    cases = _cases()
    profiles = {entry["id"] for entry in cases["benchmark_profiles"]}
    fertilizers = load_fertilizers()
    portfolios = solver_matrix.load_fertilizer_portfolios(cases, fertilizers)
    primary = portfolios[cases["primary_portfolio"]]

    assert profiles == {
        "Abram_Steiner_Hydrokultur_Naehrloesung",
        "Bugbee_Utah_Hydroponic_Cannabis_2022",
        "Conn_2013_Arabidopsis",
        "Cooper_NFT_1979",
        "DeLaRosa_2025_Lettuce_T2_HighNitrate",
        "Hermans_2010_Arabidopsis",
        "Hoagland_Arnon_1950_Solution1_Nitrate",
        "Long_Ashton_Nutrient_Solution_LANS_NitrateType",
        "augmented_saloner_bernstein",
        "solve_golden",
    }
    assert len(primary.fertilizers) == 22
    assert primary.evaluation_role == "selection"
    assert "HuminTech AMINO POWER Plus Liquid" not in primary.fertilizers
    assert "HuminTech Fulvital Plus Liquid" not in primary.fertilizers
    diagnostic = [portfolio for portfolio in portfolios.values() if portfolio.evaluation_role == "diagnostic"]
    assert {portfolio.portfolio_id for portfolio in diagnostic} == {
        "augmented_saloner_humin_honeypot",
        "solve_golden_humin_honeypot",
    }
    assert all("HuminTech AMINO POWER Plus Liquid" in portfolio.fertilizers for portfolio in diagnostic)
    assert all("HuminTech Fulvital Plus Liquid" in portfolio.fertilizers for portfolio in diagnostic)
    assert all(
        "HuminTech AMINO POWER Plus Liquid" not in portfolio.fertilizers
        and "HuminTech Fulvital Plus Liquid" not in portfolio.fertilizers
        for portfolio in portfolios.values()
        if portfolio.evaluation_role == "selection"
    )
    assert portfolios["solve_golden"].fertilizers == (
        "Yara Tera CALCINIT",
        "K+S EPSO Top Bittersalz 16-39",
        "Agrolution Special 313 14-7-14+14CaO+TE",
        "S3 Kaliwasser 28 Be",
    )
    assert portfolios["solve_golden"].reference_amounts == {
        "Yara Tera CALCINIT": 2.0,
        "K+S EPSO Top Bittersalz 16-39": 6.0,
        "Agrolution Special 313 14-7-14+14CaO+TE": 9.0,
        "S3 Kaliwasser 28 Be": 1.0,
    }
    assert portfolios["blossom_calcinit_epso_313"].fertilizers == (
        "Peters Professional Blossom Booster 10-30-20+2MgO+TE",
        "Yara Tera CALCINIT",
        "K+S EPSO Top Bittersalz 16-39",
        "Agrolution Special 313 14-7-14+14CaO+TE",
    )
    assert portfolios["kristalon_epso_313"].fertilizers == (
        "Yara Tera KRISTALON ROT CALCIUM",
        "K+S EPSO Top Bittersalz 16-39",
        "Agrolution Special 313 14-7-14+14CaO+TE",
    )
    assert portfolios["epso_313_s3"].fertilizers == (
        "K+S EPSO Top Bittersalz 16-39",
        "Agrolution Special 313 14-7-14+14CaO+TE",
        "S3 Kaliwasser 28 Be",
    )
    assert portfolios["plagron_ca_edta_basis3_epso_313"].fertilizers == (
        "Ph- Plagron Universal",
        "GH Ca-EDTA",
        "Compo Hakaphos Basis3 3-15-36(+4)",
        "K+S EPSO Top Bittersalz 16-39",
        "Agrolution Special 313 14-7-14+14CaO+TE",
    )
    assert portfolios["plagron_ghe_tripart"].fertilizers == (
        "Ph- Plagron Universal",
        "GHE Flora Grow 3-1-6",
        "GHE Flora Bloom 0-5-4",
        "GHE Flora Micro 5-0-1 Soft",
    )
    assert all(value > 0.0 for portfolio in portfolios.values() for value in portfolio.reference_amounts.values())
    assert portfolios["restricted_blossom_fetrilon_pekacid_spezial"].fertilizers == (
        "Yara Tera CALCINIT",
        "S3 Kaliwasser 28 Be",
        "Haifa MAG Magnesiumnitrat 11-0-0+16MgO",
        "Peters Professional Blossom Booster 10-30-20+2MgO+TE",
        "Compo Fetrilon Combi 1",
        "ICL Nova PeKacid 0-60-20",
        "Compo Hakaphos Soft16-8-22(+3) Spezial",
    )
    assert portfolios["restricted_313_bittersalz_mkp"].fertilizers == (
        "Agrolution Special 313 14-7-14+14CaO+TE",
        "K+S EPSO Top Bittersalz 16-39",
        "Haifa MAG Magnesiumnitrat 11-0-0+16MgO",
        "Yara Tera CALCINIT",
        "S3 Kaliwasser 28 Be",
        "Haifa Monokaliumphosphat MKP",
    )
    assert cases["unresolved_profiles"] == []
    golden = yaml.safe_load((solver_matrix.ROOT / "recipes" / "solve_golden.yml").read_text(encoding="utf-8"))
    assert golden["targets_mg_per_l"]["S"] == pytest.approx(85.79586471044226)
    barrage = solver_matrix.mass_barrage_portfolios(cases, portfolios)
    assert len(barrage) == 35
    assert sum(portfolio.evaluation_role == "selection" for portfolio in barrage) == 33
    assert sum(portfolio.evaluation_role == "diagnostic" for portfolio in barrage) == 2
    assert sum(bool(portfolio.omitted_fertilizer) for portfolio in barrage) == 22
    assert portfolios["augmented_saloner_humin_honeypot"].ignore_dose_limits is True
    assert portfolios["solve_golden_humin_honeypot"].ignore_dose_limits is True
    assert all(
        not portfolio.ignore_dose_limits
        for portfolio in portfolios.values()
        if portfolio.evaluation_role == "selection"
    )


def test_shipped_fertilizers_limit_only_humin_additives_to_fixed_doses() -> None:
    fertilizers = load_fertilizers(solver_matrix.ROOT / "data" / "fertilizers.csv")

    limits = {
        name: fertilizer.solver_max_dose_per_l
        for name, fertilizer in fertilizers.items()
        if fertilizer.solver_max_dose_per_l is not None
    }
    assert limits == {
        "HuminTech AMINO POWER Plus Liquid": 0.0,
        "HuminTech Fulvital Plus Liquid": 0.0,
    }


def test_solver_matrix_quick_smoke_writes_self_describing_outputs(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = solver_matrix.main(
        [
            "--preset",
            "quick",
            "--profiles",
            "Hoagland_Arnon_1950_Solution1_Nitrate",
            "--out-dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
    assert "Solver matrix complete" in capsys.readouterr().out
    for name in ("results.csv", "results.jsonl", "summary.json", "run_manifest.json"):
        assert (tmp_path / name).exists()

    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    manifest = json.loads((tmp_path / "run_manifest.json").read_text(encoding="utf-8"))
    assert summary["total_runs"] == 1
    assert summary["failed_runs"] == 0
    assert summary["primary_portfolio"] == "real_recipe_union"
    assert manifest["schema_version"] == 2
    assert manifest["cases_sha256"]
    assert manifest["solver_baseline"]["s_objective_enabled"] is True
    with (tmp_path / "results.csv").open(encoding="utf-8", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert row["experiment_id"] == "baseline"
    assert row["portfolio_id"] == "real_recipe_union"
    assert row["portfolio_role"] == "selection"
    assert "S" in json.loads(row["objective_elements"])


def test_solver_matrix_can_override_primary_portfolio(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = solver_matrix.main(
        [
            "--preset",
            "quick",
            "--profiles",
            "Conn_2013_Arabidopsis",
            "--primary-portfolio",
            "restricted_313_bittersalz_mkp",
            "--out-dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
    capsys.readouterr()
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    manifest = json.loads((tmp_path / "run_manifest.json").read_text(encoding="utf-8"))
    assert summary["primary_portfolio"] == "restricted_313_bittersalz_mkp"
    assert len(summary["allowed_fertilizers"]) == 6
    assert manifest["primary_portfolio"] == "restricted_313_bittersalz_mkp"


def test_solver_matrix_cap_finishes_each_config_across_profiles(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = solver_matrix.main(
        [
            "--preset",
            "matrix",
            "--profiles",
            "Hoagland_Arnon_1950_Solution1_Nitrate,Cooper_NFT_1979",
            "--max-configs",
            "2",
            "--max-runs",
            "2",
            "--out-dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
    assert "Stopped early at --max-runs 2" in capsys.readouterr().out
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["total_runs"] == 2
    assert summary["stopped_early"] is True
    with (tmp_path / "results.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert {row["profile_id"] for row in rows} == {
        "Hoagland_Arnon_1950_Solution1_Nitrate",
        "Cooper_NFT_1979",
    }
    assert {row["config_id"] for row in rows} == {"canonical"}
