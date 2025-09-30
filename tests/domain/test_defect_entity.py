import pytest

from retest_optimizer.domain.entities.defect import (
    DefectRecord,
    generate_defect_pk,
)


@pytest.fixture
def defect_record() -> DefectRecord:
    return DefectRecord(
        factory_code="F1",
        process_code="P2",
        product_model="ModelX",
        defect_item="Scratch",
        analysis_period=7,
        analysis_criteria="WEEKLY",
        reproducibility_rate=0.65,
        total_inspections=120,
        reproduced_count=78,
    )


def test_generate_defect_pk_matches_expected_format(defect_record: DefectRecord) -> None:
    pk = generate_defect_pk(
        factory_code=defect_record.factory_code,
        process_code=defect_record.process_code,
        product_model=defect_record.product_model,
        defect_item=defect_record.defect_item,
        analysis_period=defect_record.analysis_period,
        analysis_criteria=defect_record.analysis_criteria,
    )
    assert pk == "7:WEEKLY:F1:P2:ModelX:Scratch"


def test_defect_record_pk_property_uses_generator(defect_record: DefectRecord) -> None:
    assert defect_record.pk == "7:WEEKLY:F1:P2:ModelX:Scratch"


def test_alarm_history_reports_reproduced_count(defect_record: DefectRecord) -> None:
    assert defect_record.alarm_history == "78/120"


def test_meets_thresholds_returns_true_when_criteria_satisfied(
    defect_record: DefectRecord,
) -> None:
    assert defect_record.meets_thresholds(
        reproducibility_threshold=0.5,
        minimum_inspections=100,
    )


def test_meets_thresholds_returns_false_when_below_thresholds(
    defect_record: DefectRecord,
) -> None:
    assert not defect_record.meets_thresholds(
        reproducibility_threshold=0.75,
        minimum_inspections=150,
    )
