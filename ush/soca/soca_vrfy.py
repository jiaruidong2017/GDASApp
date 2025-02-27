#!/usr/bin/env python3

# make plots for marine analysis

import matplotlib.pyplot as plt
import xarray as xr
import cartopy
import cartopy.crs as ccrs
import numpy as np
import os


projs = {'North': ccrs.NorthPolarStereo(),
         'South': ccrs.SouthPolarStereo(),
         'Global': ccrs.Mollweide(central_longitude=-150)}


def plotConfig(grid_file=[],
               data_file=[],
               variable=[],
               levels=[],
               bounds=[],
               colormap=[],
               max_depth=np.nan,
               max_depths=[700.0, 5000.0],
               comout=[],
               variables_horiz={},
               variables_zonal={},
               lat=np.nan,
               lats=np.arange(-60, 60, 10),
               proj='set me',
               projs=['Global']):

    """
    Prepares the configuration for the plotting functions below
    """
    config = {}
    config['comout'] = comout  # output directory
    config['grid file'] = grid_file
    config['fields file'] = data_file
    config['levels'] = [1]
    config['colormap'] = colormap
    config['bounds'] = bounds
    config['lats'] = lats  # all the lats to plot
    config['lat'] = lat  # the lat being currently plotted
    config['max depths'] = max_depths  # all the max depths to plot
    config['max depth'] = max_depth  # the max depth currently plotted
    config['horiz variables'] = variables_horiz  # all the vars for horiz plots
    config['zonal variables'] = variables_zonal  # all the vars for zonal plots
    config['variable'] = variable  # the variable currently plotted
    config['projs'] = projs  # all the projections etc.
    config['proj'] = proj
    return config


def plotHorizontalSlice(config):
    """
    pcolormesh of a horizontal slice of an ocean field
    """
    grid = xr.open_dataset(config['grid file'])
    data = xr.open_dataset(config['fields file'])

    dirname = os.path.join(config['comout'], config['variable'])
    os.makedirs(dirname, exist_ok=True)

    if config['variable'] in ['Temp', 'Salt', 'u', 'v']:
        level = config['levels'][0]
        slice_data = np.squeeze(data[config['variable']])[level, :, :]
        label_colorbar = config['variable']+' Level '+str(level)
        figname = os.path.join(dirname, config['variable']+'_Level_'+str(level))
    else:
        slice_data = np.squeeze(data[config['variable']])
        label_colorbar = config['variable']
        figname = os.path.join(dirname, config['variable']+'_'+config['proj'])

    bounds = config['bounds']

    fig, ax = plt.subplots(figsize=(8, 5), subplot_kw={'projection': projs[config['proj']]})
    plt.pcolormesh(np.squeeze(grid.lon),
                   np.squeeze(grid.lat),
                   slice_data,
                   vmin=bounds[0], vmax=bounds[1],
                   transform=ccrs.PlateCarree(),
                   cmap=config['colormap'])

    plt.colorbar(label=label_colorbar, shrink=0.5, orientation='horizontal')
    ax.coastlines()  # TODO: make this work on hpc
    ax.gridlines(draw_labels=True)
    if config['proj'] == 'South':
        ax.set_extent([-180, 180, -90, -50], ccrs.PlateCarree())
    if config['proj'] == 'North':
        ax.set_extent([-180, 180, 50, 90], ccrs.PlateCarree())
    # ax.add_feature(cartopy.feature.LAND)  # TODO: make this work on hpc
    plt.savefig(figname, bbox_inches='tight', dpi=600)


def plotZonalSlice(config):
    """
    pcolormesh of a zonal slice of an ocean field
    """
    lat = float(config['lat'])
    grid = xr.open_dataset(config['grid file'])
    data = xr.open_dataset(config['fields file'])
    lat_index = np.argmin(np.array(np.abs(np.squeeze(grid.lat)[:, 0]-lat)))
    slice_data = np.squeeze(np.array(data[config['variable']]))[:, lat_index, :]
    depth = np.squeeze(np.array(grid['h']))[:, lat_index, :]
    depth[np.where(np.abs(depth) > 10000.0)] = 0.0
    depth = np.cumsum(depth, axis=0)
    bounds = config['bounds']
    x = np.tile(np.squeeze(grid.lon[:, lat_index]), (np.shape(depth)[0], 1))
    fig, ax = plt.subplots(figsize=(8, 5))
    plt.pcolormesh(x, -depth, slice_data,
                   vmin=bounds[0], vmax=bounds[1],
                   cmap=config['colormap'])
    plt.colorbar(label=config['variable']+' Lat '+str(lat), shrink=0.5, orientation='horizontal')
    ax.set_ylim(-config['max depth'], 0)
    dirname = os.path.join(config['comout'], config['variable'])
    os.makedirs(dirname, exist_ok=True)
    figname = os.path.join(dirname, config['variable'] +
                           'zonal_lat_'+str(int(lat)) + '_' + str(int(config['max depth'])) + 'm')
    plt.savefig(figname, bbox_inches='tight', dpi=600)


class statePlotter:

    def __init__(self, config_dict):
        self.config = config_dict

    def plot(self):
        # Loop over variables, slices (horiz and vertical) and projections ... and whatever else is needed

        #######################################
        # zonal slices

        for lat in self.config['lats']:
            self.config['lat'] = lat

            for max_depth in self.config['max depths']:
                self.config['max depth'] = max_depth

                variableBounds = self.config['zonal variables']
                for variable in variableBounds.keys():
                    bounds = variableBounds[variable]
                    self.config.update({'variable': variable, 'bounds': bounds})
                    plotZonalSlice(self.config)

        #######################################
        # Horizontal slices
        for proj in self.config['projs']:

            variableBounds = self.config['horiz variables']
            for variable in variableBounds.keys():
                bounds = variableBounds[variable]
                self.config.update({'variable': variable, 'bounds': bounds, 'proj': proj})
                plotHorizontalSlice(self.config)
