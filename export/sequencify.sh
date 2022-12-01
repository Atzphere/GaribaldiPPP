'''
This program numerically integrates and solves an
intial value differential equation problem
describing the motion of a projectile
subject to gravity and air resistance drag forces.


'''

from scipy import integrate
import numpy as np
from matplotlib import pyplot as plt
import matplotlib.animation as animation
'''
Initial values as specified by the project description
'''

b = 0.006  # kg/m
g = 9.81  # m/s^2
gforce = -g
m = 0.45  # kg
v_0 = 18  # m/s
thetadeg0 = 40
theta0 = 2 * (thetadeg0 / 360) * np.pi  # radians above the horizonal

x0 = 0  # m
y0 = 0

# STUFF TO THINK ABOUT:
# Possible multithreading?

# More variable initialization
vx_0, vy_0 = v_0 * np.cos(theta0), v_0 * np.sin(theta0)

t0 = 0
tfin = 2 * (vy_0 / g) + 2 * (y0 / vy_0)  # automatic time scaling
dt = 10E-4

xforces = []
yforces = []

t_arr = np.arange(t0, tfin, dt)
y0_arr = [x0, y0, vx_0, vy_0]

'''
Function wrapping the differential equation for the scipy solver
'''

def get_dy(t, y_arr):
    #    x = y_arr[0]
    #    y = y_arr[1]
    vx = y_arr[2]
    vy = y_arr[3]
    v = np.sqrt(vx**2 + vy**2)
    uvector = np.array([vx / v, vy / v])

    dragX = -(b * v * v * uvector[0]) / m
    dragY = -(b * v * v * uvector[1]) / m

    # return derivatives - we need dxx, dxy, dvx, dvy
    return np.array([vx, vy, dragX, gforce + dragY])


def apex(t, y):  # trigger function for when the ball reaches max height
    return y[3]  # when vy is zero


def hit_ground(t, y):
    return y[1]  # when y is zero - rectify starting case with direction below


# only trigger when going from positive to negative, end integration.

hit_ground.direction = -1
hit_ground.terminal = True # end integration when this triggers

solution = integrate.solve_ivp(
    get_dy,
    (t_arr[0], t_arr[-1]),  # integration
    y0_arr,
    t_eval=t_arr,
    method='LSODA',
    events=[apex, hit_ground]),
t_sol = solution[0]['t']
output_sols = solution[0]['y']

x_sols, y_sols = output_sols[0], output_sols[1]
vx_sols, vy_sols = output_sols[2], output_sols[3]

theta = (np.arctan(vy_sols / vx_sols) / (2 * np.pi)) * 360

# END NUMERICAL INTEGRATION PART
# BEGIN ANALYTICAL STUFF

times = np.linspace(0, tfin, 200)
xcoords = vx_0 * times + x0
ycoords = vy_0 * times + (1 / 2) * -g * times**2 + y0

numerical_mask = np.arange(0, len(x_sols))  # filter for plotting
numerical_mask = ((numerical_mask % (len(x_sols) // 20)) == 0)
numerical_mask[[0, -1]] = True
analytical_mask = (ycoords >= 0)

# parsing events

apex = solution[0]["y_events"][0][0]
impact = solution[0]["y_events"][1][0]

d_impact = impact[0]
h_apex = apex[1]
t_end = t_sol[-1]
v_impact = np.sqrt(impact[2]**2 + impact[3]**2)
drag_reduction = xcoords[analytical_mask][-1] - d_impact
finaltheta = theta[-1]

print(("Projectile impact {time} seconds after launch " +
       "at x = {dist:.3f} m, travelling at {speed:.3f} m/s " +
       "{angle:.3f} degrees from the horizontal. " +
       "It reached a maximum height of {height:0.3f} m.").format(
           time=t_end,
           dist=d_impact,
           speed=v_impact,
           angle=-finaltheta,
           height=h_apex))

print("Drag forces resulted in a final travel distance " +
      "reduced by {distance:.02f} meters".format(distance=drag_reduction))

# BEGIN PLOTTING

plt.style.use('ggplot')

fig, ax = plt.subplots(2, 2)
ax[0, 0].plot(xcoords[analytical_mask],
              ycoords[analytical_mask],
              "r",
              label="Analytical solution")  # analytical
ax[0, 0].scatter(x_sols[numerical_mask],
                 y_sols[numerical_mask],
                 c="b",
                 s=3,
                 label="Numerical solution")  # pos

ax[0, 0].set_title("Position trace")
ax[0, 0].set_xlabel("x position (m)")
ax[0, 0].set_ylabel("y position (m)")
ax[0, 0].grid()
# ax[0,1].set_axis_off() # for future reference
ax[0, 0].legend(loc="upper right")

ax[0, 1].plot(t_sol, theta)  # angle graph
ax[0, 1].set_title("$\\theta(\\vec{v})$ over time")
ax[0, 1].set_xlabel("time (s)")
ax[0, 1].set_ylabel("$\\theta (^\\circ)$")
ax[0, 1].axhline(0, color="black", linewidth=0.5)

ax[1, 0].plot(t_sol, vx_sols)  # x vel and yvels
ax[1, 0].set_title("$v_x$ over time")
ax[1, 0].set_ylabel("x velocity (m)")
ax[1, 0].set_xlabel("time (s)")

ax[1, 1].plot(t_sol, vy_sols)
ax[1, 1].set_title("$v_y$ over time")
ax[1, 1].set_ylabel("y velocity (m)")
ax[1, 1].set_xlabel("time (s)")
ax[1, 1].axhline(0, color="black", linewidth=0.5)

fig.suptitle("Projectile motion profile")
fig.tight_layout(h_pad=0.001, w_pad=0.1)

