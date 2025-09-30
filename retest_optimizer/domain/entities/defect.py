from dataclasses import dataclass


@dataclass
class DefectRecord:
    factory_code: str
    process_code: str
    product_model: str
    defect_item: str
    analysis_period: int
    analysis_criteria: str
    reproducibility_rate: float
    total_inspections: int
    reproduced_count: int

    @property
    def pk(self) -> str:
        return generate_defect_pk(
            factory_code=self.factory_code,
            process_code=self.process_code,
            product_model=self.product_model,
            defect_item=self.defect_item,
            analysis_period=self.analysis_period,
            analysis_criteria=self.analysis_criteria,
        )

    @property
    def alarm_history(self) -> str:
        return f"{self.reproduced_count}/{self.total_inspections}"

    def meets_thresholds(
        self,
        *,
        reproducibility_threshold: float,
        minimum_inspections: int,
    ) -> bool:
        return (
            self.reproducibility_rate >= reproducibility_threshold
            and self.total_inspections >= minimum_inspections
        )


def generate_defect_pk(
    *,
    factory_code: str,
    process_code: str,
    product_model: str,
    defect_item: str,
    analysis_period: int,
    analysis_criteria: str,
) -> str:
    return (
        f"{analysis_period}:{analysis_criteria}:{factory_code}:{process_code}:"
        f"{product_model}:{defect_item}"
    )
