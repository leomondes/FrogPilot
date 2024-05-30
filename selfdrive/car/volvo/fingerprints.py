from cereal import car
from openpilot.selfdrive.car.volvo.values import CAR

Ecu = car.CarParams.Ecu

FW_VERSIONS = {
  CAR.VOLVO_V60: {
    (Ecu.transmission, 0x7e1, None): [
      b'\xf1\xa0YV1FS49CDF2360777',
    ],
    (Ecu.engine, 0x7e0, None): [
      b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
    ],
    (Ecu.unknown, 0x726, None): [
      b'30786853 BK\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
    ],
    (Ecu.eps, 0x730, None): [
      b'31340673 AD\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
    ],
    (Ecu.fwdCamera, 0x764, None): [
      b'31400454 AA\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
    ],
  },
}
