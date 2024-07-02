from cereal import car, custom
from openpilot.selfdrive.car import create_button_events, get_safety_config
from openpilot.selfdrive.car.interfaces import CarInterfaceBase
from openpilot.selfdrive.car.volvo.values import Buttons
from openpilot.common.params import Params

params = Params()

ButtonType = car.CarState.ButtonEvent.Type
EventName = car.CarEvent.EventName
FrogPilotButtonType = custom.FrogPilotCarState.ButtonEvent.Type
BUTTONS_DICT = {Buttons.SET_PLUS: ButtonType.accelCruise, Buttons.SET_MINUS: ButtonType.decelCruise,
                Buttons.RESUME: ButtonType.resumeCruise, Buttons.CANCEL: ButtonType.cancel}

class CarInterface(CarInterfaceBase):
  @staticmethod
  def _get_params(ret, params, candidate, fingerprint, car_fw, disable_openpilot_long, experimental_long, docs):
    ret.carName = "volvo"
    ret.safetyConfigs = [get_safety_config(car.CarParams.SafetyModel.volvo)]
    # ret.dashcamOnly = True
    ret.radarUnavailable = True

    ret.steerControlType = car.CarParams.SteerControlType.angle

    ret.steerActuatorDelay = 0.2
    ret.steerLimitTimer = 0.8

    if params.get_bool("CSLCEnabled"):
        # Used for CEM with CSLC
        ret.openpilotLongitudinalControl = True
        ret.longitudinalTuning.deadzoneBP = [0.]
        ret.longitudinalTuning.deadzoneV = [0.9]  # == 2 mph allowable delta
        ret.stoppingDecelRate = 4.5  # == 10 mph/s
        ret.longitudinalActuatorDelayLowerBound = 1.
        ret.longitudinalActuatorDelayUpperBound = 2.

        ret.longitudinalTuning.kpBP = [8.94, 7.2, 28.]  # 8.94 m/s == 20 mph
        ret.longitudinalTuning.kpV = [0., 4., 2.]  # set lower end to 0 since we can't drive below that speed
        ret.longitudinalTuning.kiBP = [0.]
        ret.longitudinalTuning.kiV = [0.1]

    return ret

  def _update(self, c, frogpilot_variables):
    ret = self.CS.update(self.cp, self.cp_cam, frogpilot_variables)
    ret, fp_ret = self.CS.update(self.cp, self.cp_cam, frogpilot_variables)

    ret.buttonEvents = [
      *create_button_events(self.CS.cruise_buttons, self.CS.prev_cruise_buttons, BUTTONS_DICT),
      *create_button_events(self.CS.distance_button, self.CS.prev_distance_button, {1: ButtonType.gapAdjustCruise}),
      *create_button_events(self.CS.lkas_enabled, self.CS.lkas_previously_enabled, {1: FrogPilotButtonType.lkas}),
    ]

    events = self.create_common_events(ret)
    # pcm_enable=not self.CS.out.cruiseState.enabled
    # enable_buttons=(ButtonType.setCruise, ButtonType.resumeCruise)

    ret.events = events.to_msg()

    return ret, fp_ret

  def apply(self, c, now_nanos, frogpilot_variables):
    return self.CC.update(c, self.CS, now_nanos, frogpilot_variables)
