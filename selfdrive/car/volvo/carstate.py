from cereal import car, custom
from opendbc.can.parser import CANParser
from openpilot.common.conversions import Conversions as CV
from openpilot.selfdrive.car.interfaces import CarStateBase
from openpilot.selfdrive.car.volvo.values import CarControllerParams, DBC, Buttons


class CarState(CarStateBase):
  def __init__(self, CP):
    super().__init__(CP)
    self.cruiseState_enabled_prev = False
    self.eps_torque_timer = 0

  def calculate_speed_limit(self, cp_cam, frogpilot_variables):
    speed_limit = cp_cam.vl["FSM5"]['TSR_Speed'] * CV.KPH_TO_MS
    return speed_limit if speed_limit not in (0, 255) else 0

  def update(self, cp, cp_cam, frogpilot_variables):
    ret = car.CarState.new_message()
    fp_ret = custom.FrogPilotCarState.new_message()

    self.prev_distance_button = self.distance_button
    self.distance_button = cp.vl["CCButtons"]["TimeGapDecreaseBtn"]

    self.prev_cruise_buttons = self.cruise_buttons

    if bool(cp.vl["CCButtons"]["ACCSetBtn"]):
      self.cruise_buttons = Buttons.SET_PLUS
    elif bool(cp.vl["CCButtons"]["ACCMinusBtn"]):
      self.cruise_buttons = Buttons.SET_MINUS
    elif bool(cp.vl["CCButtons"]["ACCResumeBtn"]):
      self.cruise_buttons = Buttons.RESUME
    else:
      self.cruise_buttons = Buttons.NONE

    # car speed
    ret.vEgoRaw = cp.vl["VehicleSpeed1"]["VehicleSpeed"] * CV.KPH_TO_MS
    ret.vEgo, ret.aEgo = self.update_speed_kf(ret.vEgoRaw)
    ret.standstill = ret.vEgoRaw < 0.1
    fp_ret.dashboardSpeedLimit = self.calculate_speed_limit(cp_cam, frogpilot_variables)

    # gas pedal
    ret.gas = cp.vl["AccPedal"]["AccPedal"] / 100.0
    ret.gasPressed = cp.vl["AccPedal"]["AccPedal"] > 10  # compare the int to not mismatch panda

    # brake pedal
    ret.brake = cp.vl["BrakePedal"]["BrakePressure"]
    ret.brakePressed = cp.vl["Brake_Info"]["BrakePedal"] == 2

    # steering
    ret.steeringAngleDeg = cp.vl["PSCM1"]["SteeringAngleServo"]
    ret.steeringTorqueEps = cp.vl["PSCM1"]["LKATorque"]
    ret.steeringPressed = False  # TODO

        # cruise state
    ret.cruiseState.speed = cp.vl["ACC_Speed"]["ACC_Speed"] * CV.KPH_TO_MS
    ret.cruiseState.speedCluster = cp.vl["ACC_Speed"]["ACC_Speed"] * CV.KPH_TO_MS
    ret.cruiseState.available = cp_cam.vl["FSM0"]["ACCStatus"] in (2, 6, 7)
    ret.cruiseState.enabled = cp_cam.vl["FSM0"]["ACCStatus"] in (6, 7)
    ret.cruiseState.standstill = cp_cam.vl["FSM3"]["ACC_Standstill"] == 1
    ret.cruiseState.nonAdaptive = False  # TODO
    ret.accFaulted = False
    self.acc_distance = cp_cam.vl["FSM1"]["ACC_Distance"]

    # Check if servo stops responding when ACC is active
    if ret.cruiseState.enabled and ret.vEgo > self.CP.minSteerSpeed:
      # Reset counter on entry
      if not self.cruiseState_enabled_prev:
        self.eps_torque_timer = 0

      # Count up when no torque from servo detected
      if ret.steeringTorqueEps == 0:
        self.eps_torque_timer += 1
      else:
        self.eps_torque_timer = 0

      # Set fault if above threshold
      ret.steerFaultTemporary = self.eps_torque_timer >= CarControllerParams.STEER_TIMEOUT

    self.cruiseState_enabled_prev = ret.cruiseState.enabled

    # gear
    # only check reverse
    gear = cp.vl["Gear_Info"]["Gear"]
    if gear == 44 and ret.vEgo < 3:
      ret.gearShifter = car.CarState.GearShifter.reverse
    else:
      ret.gearShifter = car.CarState.GearShifter.drive

    # safety
    ret.stockFcw = False  # TODO
    ret.stockAeb = False

    # button presses
    ret.leftBlinker = cp.vl["MiscCarInfo"]["TurnSignal"] == 1
    ret.rightBlinker = cp.vl["MiscCarInfo"]["TurnSignal"] == 3

    # lock info
    ret.doorOpen = not all([cp.vl["Doors"]["DriverDoorClosed"], cp.vl["Doors"]["PassengerDoorClosed"]])
    ret.seatbeltUnlatched = False  # TODO

    # Store info from servo message PSCM1
    # FSM (camera) checks if LKAActive & LKATorque active when not requested
    self.pscm_stock_values = cp.vl["PSCM1"]

    self.cruiseState_enabled_prev = ret.cruiseState.enabled

    return ret, fp_ret

  @staticmethod
  def get_can_parser(CP):
    messages = [
      # msg, freq
      ("VehicleSpeed1", 50),
      ("AccPedal", 100),
      ("BrakePedal", 50),
      ("Brake_Info", 50),
      ("PSCM1", 50),
      ("ACC_Speed", 50),
      ("MiscCarInfo", 25),
      ("Doors", 20),
      ("Gear_Info", 50),
      ("CCButtons", 20),
    ]

    return CANParser(DBC[CP.carFingerprint]["pt"], messages, 0)

  @staticmethod
  def get_cam_can_parser(CP):
    messages = [
      # msg, freq
      ("FSM0", 100),
      ("FSM1", 50),
      ("FSM3", 50),
      ("FSM5", 20),
    ]

    return CANParser(DBC[CP.carFingerprint]["pt"], messages, 2)
