import omni.kit.stage_templates
import omni.usd
from pxr import UsdGeom


class ZUpDefaultStage:
    def __init__(self):
        from omni.kit.stage_templates.templates.default_stage import DefaultStage

        self._default_stage = DefaultStage.__new__(DefaultStage)
        omni.kit.stage_templates.register_template("zup default stage", self.new_stage)

    def __del__(self):
        omni.kit.stage_templates.unregister_template("zup default stage")

    def new_stage(self, rootname, usd_context_name):
        self._default_stage.new_stage(rootname, usd_context_name)
        stage = omni.usd.get_context(usd_context_name).get_stage()
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)


ZUpDefaultStage()
