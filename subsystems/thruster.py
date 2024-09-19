import numpy as np
from math import sin, cos, tan, radians
from scipy.optimize import minimize
import time
import functools

import simulation

# if not simulation.is_simulated():
#     import RPi.GPIO as GPIO
#     GPIO.setwarnings(False)
#     GPIO.setmode(GPIO.BCM)

np.set_printoptions(precision=3, suppress=True)

def in_to_ft(x):
    return (1/12.0) * x

# def calculate_duty_cycle(pulse_width, frequency):
    # return (pulse_width / (1/))

class Thruster():
    speed = 0
    pwm = None

    def __init__(self, x, y, z, theta, phi, speed_bounds = (-0.7, 1), pin=None, freq=400):
        if pin and not simulation.is_simulated():
            GPIO.setup(pin, GPIO.OUT)
            self.pwm = GPIO.PWM(pin, 400)
            self.pwm.start(60)
            time.sleep(0.3)
        self.x = x
        self.y = y
        self.z = z
        self.phi = phi
        self.theta = theta
        self.speedbound_reverse, self.speedbound_forward = speed_bounds

    def stop(self):
        if self.pwm:
            self.pwm.stop()

    def get_force_coefficients(self):
        p = radians(90-self.phi)
        t = radians(90+self.theta)

        sinp = sin(p)
        sint = sin(t)
        cost = cos(t)
        cosp = cos(p)

        # input(sinp * cost)

        return [
            sinp * cost,
            sinp * sint,
            cosp
        ]

    def set_speed(self, speed):
        self.speed = speed
        throttle = 0
        if self.pwm:
            if speed < 0:
                throttle = -speed/self.speedbound_reverse
            else:
                throttle = speed/self.speedbound_forward
            output = 60 + (16 * throttle)
            # print(output)
            # self.pwm.ChangeDutyCycle(output)

        # self
        # self.pwm.ChangeDutyCycle()

    def get_moment_coefficients(self):
        p = radians(90-self.phi)
        t = radians(90+self.theta)
        x = self.x
        y = self.y
        z = self.z

        sinp = sin(p)
        sint = sin(t)
        cost = cos(t)
        cosp = cos(p)

        return [
            (z*sinp*sint) - (y*cosp),
            (x*cosp) - (z*sinp*cost),
            (y*sinp*cost) - (x*sinp*sint)
        ]

    def get_speed_bounds(self):
        return self.speedbound_reverse, self.speedbound_forward

    def serialize(self):
        return {
            "force_coefficients": self.get_force_coefficients(),
            "moment_coefficients": self.get_moment_coefficients(),
            "speed": self.speed,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "phi": self.phi,
            "theta": self.theta,
            "speedbound_forward": self.speedbound_forward,
            "speedbound_reverse": self.speedbound_reverse,
        }


@functools.cache
def solve_motion(motors, Fx, Fy, Fz, Rx, Ry, Rz, limit=True):
    # print('@@@@@@@@@@@@@@@@@@@@@@')
    coefficients = []
    for motor in motors:
        coefficients.append(motor.get_force_coefficients() + motor.get_moment_coefficients())
        # print(motor, coefficients[-1])

    A = np.array(coefficients).transpose()
    b = np.array([Fx, Fy, Fz, Rx, Ry, Rz])
    n = len(b)


    time_a = time.time()
    np_radii = np.linalg.lstsq(A, b, rcond=None)[0]
    fun = lambda x: np.linalg.norm(np.dot(A,x)-b)
    time_b = time.time()
    # try:
        # sol = minimize(fun, np.zeros(n), method='L-BFGS-B', bounds=[(i.get_speed_bounds() if limit else (None, None)) for i in motors])
    # except ValueError as e:
        # print(e)
        # raise e
        # sol = {"x":[0,0,0,0,0,0]}
    # print(time.time()-time_b, time_b- time_a)
    # np_radii = sol['x']

    rA = np_radii * A

    return {"speeds": list(np_radii), "actual": list(map(sum, rA))}


def get_movement(motors):
    coefficients = []

    for motor in motors:
        coefficients.append(motor.get_force_coefficients() + motor.get_moment_coefficients())

    A = np.array(coefficients).transpose()

    speeds = np.array(list(map(lambda i:i.speed, motors)))

    rA = speeds * A

    # print(speeds)

    return list(map(sum, rA))


# print(get_movement(motors))
# solve(motors, 1,0,0,0,0,0)
# solve(motors, 0,1,0,0,0,0)
# solve(motors, 0,0,1,0,0,0)
# solve(motors, 0,0,0,1,0,0)
# solve(motors, 0,0,0,0,1,0)
# solve(motors, 0,0,0,0,0,1)
# solve(motors, 0,0,0,0,0,0)
