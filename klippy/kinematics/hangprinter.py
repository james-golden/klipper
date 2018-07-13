# Code for handling the kinematics of "hangprinter" robots
#
# Copyright (C) 2018  Kevin O'Connor <kevin@koconnor.net>
#
# This file may be distributed under the terms of the GNU GPLv3 license.
import stepper

class HangprinterKinematics:
    def __init__(self, toolhead, config):
        # Setup steppers at each anchor
        self.steppers = []
        self.anchors = []
        for i in range(26):
            name = 'stepper_' + chr(ord('a') + i)
            if i >= 3 and not config.has_section(name):
                break
            stepper_config = config.getsection(name)
            s = stepper.PrinterStepper(stepper_config)
            self.steppers.append(s)
            a = tuple([stepper_config.getfloat('anchor_' + n) for n in 'xyz'])
            self.anchors.append(a)
            s.setup_itersolve('hangprinter_stepper_alloc', *a)
        # Setup stepper max halt velocity
        max_velocity, max_accel = toolhead.get_max_velocity()
        max_halt_velocity = toolhead.get_max_axis_halt()
        for s in self.steppers:
            s.set_max_jerk(max_halt_velocity, max_accel)
        # Setup boundary checks
        self.need_motor_enable = True
        self.set_position([0., 0., 0.], ())
    def get_steppers(self, flags=""):
        return list(self.steppers)
    def calc_position(self):
        # Use only first three steppers to calculate cartesian position
        spos = [s.get_commanded_position() for s in self.steppers[:3]]
        return mathutil.trilateration(self.anchors[:3], [sp*sp for sp in spos])
    def set_position(self, newpos, homing_axes):
        for s in self.steppers:
            s.set_position(newpos)
    def home(self, homing_state):
        # XXX - homing not implemented
        homing_state.set_axes([0, 1, 2])
        homing_state.set_homed_position([0., 0., 0.])
    def motor_off(self, print_time):
        for s in self.steppers:
            s.motor_enable(print_time, 0)
        self.need_motor_enable = True
    def _check_motor_enable(self, print_time):
        for s in self.steppers:
            s.motor_enable(print_time, 1)
        self.need_motor_enable = False
    def check_move(self, move):
        # XXX - boundary checks and speed limits not implemented
        pass
    def move(self, print_time, move):
        if self.need_motor_enable:
            self._check_motor_enable(print_time)
        for s in self.steppers:
            s.step_itersolve(move.cmove)

def load_kinematics(toolhead, config):
    return HangprinterKinematics(toolhead, config)