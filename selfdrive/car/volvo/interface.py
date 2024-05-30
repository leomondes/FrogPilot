from cereal import car, custom
from openpilot.selfdrive.car import get_safety_config
from openpilot.selfdrive.car.interfaces import CarInterfaceBase

ButtonType = car.CarState.ButtonEvent.Type
EventName = car.CarEvent.EventName
FrogPilotButtonType = custom.FrogPilotCarState.ButtonEvent.Type

class CarInterface(CarInterfaceBase):
  @staticmethod
  def _get_params(ret, candidate, fingerprint, car_fw, disable_openpilot_long, experimental_long, docs):
    ret.carName = "volvo"
    ret.safetyConfigs = [get_safety_config(car.CarParams.SafetyModel.volvo)]
    # ret.dashcamOnly = True
    ret.radarUnavailable = True

    ret.steerControlType = car.CarParams.SteerControlType.angle

    ret.steerActuatorDelay = 0.1
    ret.steerLimitTimer = 0.8

    return ret

  def _update(self, c, frogpilot_toggles):
    ret, fp_ret = self.CS.update(self.cp, self.cp_cam, frogpilot_toggles)

    events = self.create_common_events(ret)
    # pcm_enable=not self.CS.out.cruiseState.enabled
    # enable_buttons=(ButtonType.setCruise, ButtonType.resumeCruise)

    ret.events = events.to_msg()

    return ret, fp_ret
