import json
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
from math import ceil
from math import pi
import math
from ast import literal_eval
from matplotlib.animation import FuncAnimation
from matplotlib.offsetbox import (DrawingArea,OffsetImage,AnnotationBbox)
import numpy as np




# ---------- PART 1: Globals

n_agents = 20
my_dpi = 96
Writer = matplotlib.animation.writers['ffmpeg']
writer = Writer(fps=2.5, metadata=dict(artist='Me'), bitrate=1800)
fig = plt.figure(figsize=(2000/my_dpi, 1600/my_dpi), dpi=my_dpi)
my_palette = plt.cm.get_cmap("Set2",len(n_agents))
frames = 100



def update(i):
	global plot_data, df
	l_d = plot_data[0]
	f_d = plot_data[1]
	for l,l_f,id_no in zip(l_d,f_d,categories):
		values = df[str(i)][id_no]['ActBelief']
		cat_range = range(N)
		value_dict = dict([[c_r, 0.0] for c_r in cat_range])
		for v_d in value_dict.keys():
			for k_i in values.keys():
				if literal_eval(k_i)[v_d] == 1:
					value_dict[v_d] += 100 * values[k_i]

		val = list(value_dict.values())
		val += val[:1]
		l.set_data(angles,val)
		l_f.set_xy(np.array([angles,val]).T)
	# plot_data = [l_d,f_d]
	return l_d + f_d


def grid_init(nrows, ncols, obs_range):
	# fig_new = plt.figure(figsize=(1000/my_dpi,1000/my_dpi),dpi=my_dpi)
	ax = plt.subplot(223)
	t = 0
	row_labels = range(nrows)
	col_labels = range(ncols)
	plt.xticks(range(ncols), col_labels)
	plt.yticks(range(nrows), row_labels)
	ax.set_xticks([x - 0.5 for x in range(1, ncols)], minor=True)
	ax.set_yticks([y - 0.5 for y in range(1, nrows)], minor=True)
	ax.set_xlim(-0.5,nrows-0.5)
	ax.set_ylim(-0.5,ncols-0.5)
	ax.invert_yaxis()
	ag_array = []
	plt.grid(which="minor", ls="-", lw=1)
	i = 0
	for id_no in categories:
		p_t = df[str(0)][id_no]['PublicTargets']
		color = my_palette(i)
		init_loc = tuple(reversed(coords(df[str(0)][id_no]['AgentLoc'][0], ncols)))
		c_i = plt.Circle(init_loc, 0.45, color=color)
		route_x, route_y = zip(*[tuple(reversed(coords(df[str(t)][str(id_no)]['NominalTrace'][s][0],ncols))) for s in df[str(t)][str(id_no)]['NominalTrace']])
		cir_ax = ax.add_artist(c_i)
		lin_ax = ax.add_patch(patches.Rectangle(np.array(init_loc)-obs_range-0.5, 2*obs_range+1, 2*obs_range+1,fill=False, color=color, clip_on=True, alpha=0.5, ls='--', lw=4))
		plt_ax, = ax.plot(route_x, route_y, color=color, linewidth=5, linestyle='solid')
		ag_array.append([cir_ax, lin_ax, plt_ax])
		for k in p_t:
			s_c = coords(k, ncols)
			ax.fill([s_c[1]+0.4, s_c[1]-0.4, s_c[1]-0.4, s_c[1]+0.4], [s_c[0]-0.4, s_c[0]-0.4, s_c[0]+0.4, s_c[0]+0.4], color=color, alpha=0.9)
		i += 1
	return ag_array


def grid_update(i):
	global ax_ar, df, ncols, obs_range
	write_objects = []
	for a_x, id_no in zip(ax_ar, categories):
		c_i, l_i, p_i = a_x
		loc = tuple(reversed(coords(df[str(i)][id_no]['AgentLoc'][0], ncols)))
		c_i.set_center(loc)
		l_i.set_xy(np.array(loc)-obs_range-0.5)
		route_x, route_y = zip(*[tuple(reversed(coords(df[str(i)][str(id_no)]['NominalTrace'][s][0], ncols))) for s in df[str(i)][str(id_no)]['NominalTrace']])
		p_i.set_xdata(route_x)
		p_i.set_ydata(route_y)
		write_objects += [c_i] + [l_i] + [p_i]
	return write_objects


def coords(s,ncols):
	return (int(s /ncols), int(s % ncols))



# ---------- PART 2:

nrows = 10
ncols = 10
moveobstacles = []
obstacles = []


con_dict = con_ar = con_init()
bel_lines = belief_chart_init()
ax_ar = grid_init(nrows, ncols, obs_range)
# update()
# plt.show()
# update_all(100)
# ani = FuncAnimation(fig, update_all, frames=frames, interval=500, blit=True,repeat=False)
# ani.save('8_agents-3range-wheel.mp4',writer = writer)
# plt.show()
# ani.save('decen.gif',dpi=80,writer='imagemagick')


# fig = plt.figure(figsize=(4,4))
# ax = fig.add_subplot(111, projection='polar')
# ax.set_ylim(0,100)
#
# data = np.random.rand(50)*6+2
# theta = np.linspace(0,2.*np.pi, num=50)
# l,  = ax.plot([],[])
#
# def update(i):
#     global data
#     data += (np.random.rand(50)+np.cos(i*2.*np.pi/50.))*2
#     data[-1] = data[0]
#     l.set_data(theta, data )
#     return l,
#
# ani = FuncAnimation(fig, update, frames=50, interval=200, blit=True)
# plt.show()