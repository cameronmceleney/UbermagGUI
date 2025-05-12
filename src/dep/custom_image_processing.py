# -*- coding: utf-8 -*-

# -------------------------- Preprocessing Directives -------------------------

# Standard Libraries
import logging as lg
from sys import exit

# 3rd Party packages
from datetime import datetime

import matplotlib.transforms as mpl_t
import matplotlib.quiver as mpl_q
import matplotlib.image as mpl_i
import matplotlib.colorbar as mpl_cbar
import matplotlib.ticker as mpl_ticker
from matplotlib.pyplot import colorbar
from matplotlib.text import Text
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from mpl_toolkits.axes_grid1.axes_divider import make_axes_locatable
import matplotlib.pyplot as plt
import numpy as np

# My packages/Header files
# Here

# ----------------------------- Program Information ----------------------------

"""
Ubermag offers many default tools for image processing. While they are useful for generating outputs, they often feel 
like "an axe where a scalpel is required". Furthermore, it is difficult to manipulate the Ubermag functions as they are
really just wrappers for mpl functions and modules. To try and ease this process, I have created this file. It aims to
ease the burden of manipulating mpl properties, and offer a more direct (and documented) approach than what is currently
available in Ubermag.
"""
PROGRAM_NAME = "custom_image_processing.py"
"""
Created on 24 Jul 24 by Cameron Aidan McEleney
"""


# ---------------------------- Function Declarations ---------------------------

def loggingSetup():
    """
    Minimum Working Example (MWE) for logging. Pre-defined levels are:
        
        Highest               ---->            Lowest
        CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET
    """
    today_date = datetime.now().strftime("%y%m%d")
    current_time = datetime.now().strftime("%H%M")

    lg.basicConfig(filename=f'./{today_date}-{current_time}.log',
                   filemode='w',
                   level=lg.INFO,
                   format='%(asctime)s | %(module)s::%(funcName)s | %(levelname)s | %(message)s',
                   datefmt='%Y-%m-%d %H:%M:%S',
                   force=True)


# ------------------------------ Implementations ------------------------------

def default_three_pane(system, system_prop, system_region, figs_output_dir, drive_number, fig_name, has_schematic=True,
                       scalar_resample_shape=None, vector_resample_shape=None):
    weight_factors = {'horizontal': [0.1, 0.9], 'vertical': [0.8, 0.2]}
    weighted_heights = [weight * numcells for weight, numcells in zip(weight_factors['vertical'],
                                                                      [system_prop.numcells[1],
                                                                       system_prop.numcells[2]])]
    height_ratios = [val / sum(weighted_heights) for val in weighted_heights]

    weighted_widths = [weight * numcells for weight, numcells in zip(weight_factors['horizontal'],
                                                                     [system_prop.numcells[1],
                                                                      system_prop.numcells[2]])]
    width_ratios = [val / sum(weighted_widths) for val in weighted_widths]
    use_quiv_arrow = False

    fig, fig_axs = plt.subplot_mosaic(mosaic=[['schematic', 'upper right'],
                                              ['lower left', 'lower right']],
                                      figsize=(8, 6),
                                      gridspec_kw={'width_ratios': (width_ratios[0], width_ratios[1]),
                                                   'height_ratios': (height_ratios[0], height_ratios[1]),
                                                   'wspace': 0.0,
                                                   'hspace': 0.0},
                                      layout='constrained',
                                      facecolor='lightgrey'
                                      )

    fig.suptitle(f'Normalised magnetisation fields ({fig_name})', fontsize=24)

    ################################
    mpl_wrapper(system.m.orientation.sel('x'),
                ax=fig_axs['schematic'],
                multiplier=1e-9,
                scalar_resample=(system_prop.numcells[1], system_prop.numcells[2]),
                vector_resample=(system_prop.numcells[1], system_prop.numcells[2]),
                scalar_comp='y',
                scalar_kw={'cmap': 'inferno', 'colorbar_label': 'm$_\\text{y}$', "interpolation": "none"},
                vector_kw={'vdims': ['y', 'z'], 'cmap': 'viridis', 'use_color': False, 'alpha': 0.2,
                           'colorbar': False, 'color_field': system.m.orientation.z.sel("x"),
                           'scale': 3, 'headwidth': 16, 'headlength': 16, 'headaxislength': 16
                           },
                mpl_kw={'title': ''})

    rotate_in_place(fig_axs['schematic'],
                    [system_prop.numcells[1], system_prop.numcells[2]],
                    rotate=False,
                    ax_kw={'title': '', 'ylabel': '', 'yticklabels': ''},
                    xaxis_kw={'ticks_position': 'top', 'label_position': 'top'},
                    yaxis_kw={'ticks_position': 'right', 'label_position': 'right'})

    alter_colorbar(fig_axs['schematic'],
                   target_type='imshow',
                   cbar_imshow_kw={'location': 'left', 'orientation': 'vertical', 'pad': 0.07},
                   cbar_xaxis_kw={},
                   cbar_yaxis_kw={'ticks_position': 'left', 'label_position': 'left'},
                   )

    ################################
    if has_schematic:
        fig_axs['lower left'].set_facecolor('none')
        fig_axs['lower left'].axis('off')
        fig_axs['lower left'] = fig.add_subplot(2, 2, 3, projection='3d')

        system_region._mesh.mpl.subregions(ax=fig_axs['lower left'], multiplier=1e-9,
                                           box_aspect=(10, 4, 4), show_region=True)
        fig_axs['lower left'].view_init(roll=75, elev=150, azim=240)
        fig_axs['lower left'].zaxis.labelpad = -5  # Adjust the value to move the zlabel closer
        fig_axs['lower left'].yaxis.labelpad = -5  # Adjust the value to move the ylabel closer
        fig_axs['lower left'].xaxis.labelpad = 10

        fig_axs['lower left'].xaxis.set_major_locator(mpl_ticker.MaxNLocator(nbins=4))
        # Remove background color
        fig_axs['lower left'].set_facecolor('none')
    else:
        fig_axs['lower left'].clear()
        fig_axs['lower left'].set_visible(False)

    ################################
    mpl_wrapper(system.m.orientation.sel('y'),
                ax=fig_axs['upper right'],
                multiplier=1e-9,
                scalar_resample=scalar_resample_shape if scalar_resample_shape else (
                system_prop.numcells[0], system_prop.numcells[2]),
                vector_resample=vector_resample_shape if vector_resample_shape else (
                    16, int(np.ceil(system_prop.numcells[2]))),
                scalar_comp='x',
                scalar_kw={'cmap': 'inferno', 'colorbar_label': 'm$_\\text{x}$', "interpolation": "none"},
                vector_kw={'vdims': ['x', 'z'], 'cmap': 'viridis', 'use_color': False, 'colorbar': False, 'alpha': 0.2,
                           'colorbar_label': 'upper_right_cbar',
                           'color_field': system.m.orientation.z.sel('y')
                           },
                mpl_kw={})

    rotate_in_place(fig_axs['upper right'],
                    [system_prop.numcells[0], system_prop.numcells[2]],
                    rotate=False,
                    ax_kw={'title': ''},
                    xaxis_kw={'ticks_position': 'top', 'label_position': 'top'},
                    yaxis_kw={'ticks_position': 'right', 'label_position': 'right'})

    alter_colorbar(fig_axs['upper right'],
                   target_type='imshow',
                   cbar_imshow_kw={'location': 'right', 'orientation': 'vertical', 'pad': 0.6},
                   cbar_xaxis_kw={},
                   cbar_yaxis_kw={'ticks_position': 'right', 'label_position': 'right'})

    ################################
    mpl_wrapper(system.m.orientation.sel('z'),
                ax=fig_axs['lower right'],
                multiplier=1e-9,
                scalar_resample=scalar_resample_shape if scalar_resample_shape else (
                system_prop.numcells[0], system_prop.numcells[1]),
                vector_resample=vector_resample_shape if vector_resample_shape else (16, system_prop.numcells[1]),
                scalar_comp='z',
                scalar_kw={'cmap': 'inferno', 'colorbar_label': 'm$_\\text{z}$', "interpolation": "none"},
                vector_kw={'vdims': ['x', 'y'], 'cmap': 'viridis', 'use_color': True, 'alpha': 0.3, 'colorbar': True,
                           'color_field': system.m.orientation.x.sel('z')},
                # 'headwidth': 16, 'headlength': 16, 'headaxislength': 12},
                mpl_kw={'title': '', 'aspect': 'auto'})

    rotate_in_place(fig_axs['lower right'],
                    [system_prop.numcells[0], system_prop.numcells[1]],
                    rotate=False,
                    ax_kw={'title': '', 'xlabel': '', 'xticklabels': ''},
                    xaxis_kw={'ticks_position': 'bottom', 'label_position': 'bottom'},
                    yaxis_kw={'ticks_position': 'right', 'label_position': 'right'})

    alter_colorbar(fig_axs['lower right'],
                   target_type='quiver',
                   cbar_imshow_kw={'location': 'right', 'pad': 0.6},
                   cbar_quiver_kw={'location': 'bottom', 'orientation': 'horizontal', 'pad': 0.15,
                                   'ylabel': 'Quiver: m$_\\text{x}$'},
                   )

    ################################
    plt.savefig(figs_output_dir + '/drive-' + str(drive_number) + "_m_" + fig_name + '.png', format='png',
                dpi=300, bbox_inches='tight')


def mpl_wrapper(field, ax, multiplier, scalar_resample=None, vector_resample=None, scalar_comp=None, scalar_kw=None,
                vector_kw=None, mpl_kw=None):
    """
    Wrapper function for plotting with Ubermag's MplField class, allowing different resampling for scalar and vector fields.

    Parameters:
        field (df.Field): The field object to plot.
        ax (matplotlib.axes.Axes): The axes to plot on.
        multiplier (float): The multiplier for units.
        scalar_resample_shape (tuple): The shape to resample the scalar field to (default is None).
        vector_resample_shape (tuple): The shape to resample the vector field to (default is None).
        scalar_comp (str): The component to use for the scalar field (default is None).
        scalar_kw (dict): Keyword arguments for scalar plotting.
        vector_kw (dict): Keyword arguments for vector plotting.
    """

    if isinstance(mpl_kw, dict) and mpl_kw is not None and scalar_kw is None and vector_kw is None:
        ax.set(**mpl_kw)
        return

    scalar_field = field
    vector_field = field

    # Resample scalar field if needed
    if scalar_resample:
        scalar_field = scalar_field.resample(scalar_resample)

    # Resample vector field if needed
    if vector_resample:
        vector_field = vector_field.resample(vector_resample)

    # Select scalar component if specified
    if scalar_comp:
        scalar_field = getattr(scalar_field, scalar_comp)

    # Set default keyword arguments if not provided
    if scalar_kw is None:
        scalar_kw = {}
    if vector_kw is None:
        vector_kw = {}

    # Call the MplField class
    scalar_field.mpl.scalar(ax=ax, multiplier=multiplier, **scalar_kw)
    vector_field.mpl.vector(ax=ax, multiplier=multiplier, **vector_kw)

    # Set matplotlib params
    if mpl_kw is None:
        mpl_kw = {}
    ax.set(aspect='auto')
    ax.set(**mpl_kw)


def rotate_in_place(ax, system_dims, rotate=True, ax_kw=None, xaxis_kw=None, yaxis_kw=None):
    if rotate:
        # Rotate and update image
        for img in ax.get_images():
            image_array = img.get_array()
            rotated_image_array = np.rot90(image_array, k=-1)
            new_extent = [img.get_extent()[3], img.get_extent()[2], img.get_extent()[0], img.get_extent()[1]]
            img.set(data=rotated_image_array, extent=new_extent)

        # Rotate and update quiver
        for quiv in ax.findobj(mpl_q.Quiver):
            x, y = quiv.X, quiv.Y
            u, v = quiv.U, quiv.V
            quiv.set(zorder=1.99, offsets=[[yi, xi] for xi, yi in quiv.get_offsets()])
            quiv.set_UVC(-v, u)

        # Swap axis labels and rescale to defaults
        ax.set(xlabel=ax.get_ylabel(),
               ylabel=ax.get_xlabel(),
               aspect='auto',
               anchor='W')

    if ax_kw is None:
        ax_kw = {}
    ax.set(**ax_kw)

    if xaxis_kw is None:
        xaxis_kw = {}
    ax.xaxis.set(**xaxis_kw)

    if yaxis_kw is None:
        yaxis_kw = {}
    ax.yaxis.set(**yaxis_kw)

    ax.set_ylabel(ylabel=ax.get_ylabel(), loc='center',
                  rotation=270 if yaxis_kw.get('label_position', 'right') == 'right' else 90,
                  labelpad=16 if yaxis_kw.get('label_position', 'right') == 'right' else 2)

    ax_xlabels = ax.get_xticklabels()
    ax_xlim = [ax.get_xlim()[0] - 2e-14, ax.get_xlim()[1] + 2e-14]

    if ax_xlabels:
        # Find the first visible tick within the x-axis limits
        for i in range(0, len(ax_xlabels) - 1, 1):
            label_position = ax.get_xticks()[i]
            if ax_xlim[0] <= label_position <= ax_xlim[1]:
                ax_xlabels[i].set_horizontalalignment('left')
                break

        # Find the last visible tick within the x-axis limits
        for i in range(len(ax_xlabels) - 1, 0, -1):
            label_position = ax.get_xticks()[i]
            if ax_xlim[0] <= label_position <= ax_xlim[1]:
                ax_xlabels[i].set_horizontalalignment('right')
                break


def alter_colorbar(ax, target_type='imshow', cbar_imshow_kw=None, cbar_quiver_kw=None,
                   cbar_xaxis_kw=None, cbar_yaxis_kw=None, insert_invisible_cbar=False):
    fig = ax.figure

    # Ensure the colorbar keyword arguments dictionary is initialized
    if cbar_imshow_kw is None:
        cbar_imshow_kw = {}

    # Step 1: Find the original `imshow` colorbar and copy its properties
    imshow_cbar_props = {}
    for image in ax.get_images():
        if hasattr(image, 'colorbar') and image.colorbar is not None:
            imshow_cbar_props = {
                'parent_ax': ax,
                'cbar_ax': image.colorbar.ax,
                'props': image.colorbar.ax.properties(),
                'quadmesh': image.colorbar.ax.collections[1],  # Using 'quadmesh' to avoid black spaces
                'cmap': image.cmap,
                'ylabel': image.colorbar.ax.get_ylabel(),
                'yticklabels': [label.get_text() for label in image.colorbar.ax.get_yticklabels()]
            }
            fig.delaxes(imshow_cbar_props['cbar_ax'])  # Remove the old imshow colorbar
            break

    if not imshow_cbar_props:
        raise ValueError("No imshow colorbar found to alter.")

    # Step 2: Create the new `imshow` colorbar with the original properties
    ax_divider = make_axes_locatable(ax)
    cax_imshow = ax_divider.append_axes(cbar_imshow_kw.get('location', 'right'),
                                        size=cbar_imshow_kw.get('size', 0.2),
                                        pad=cbar_imshow_kw.get('pad', 0.5), )

    new_imshow_cbar = fig.colorbar(
        imshow_cbar_props['quadmesh'],  # Using 'quadmesh' to avoid black spaces
        cax=cax_imshow,
        orientation=cbar_imshow_kw.get('orientation', 'vertical'),
        fraction=0.15,
        shrink=1.0,
        extend='neither',
        extendrect=False,
        #format='%.2f',
        ticks=mpl_ticker.MaxNLocator(nbins='auto', prune=None, min_n_ticks=3),
        aspect='auto'
    )
    new_imshow_cbar.set_label(label=imshow_cbar_props.get('ylabel', 'Parameter'), loc='center',
                              rotation=270 if cbar_imshow_kw.get('location', 'right') == 'right' else 90,
                              labelpad=10 if cbar_imshow_kw.get('location', 'right') == 'right' else 2)

    new_imshow_cbar.mappable.set_cmap(imshow_cbar_props['cmap'])

    if cbar_quiver_kw is None:
        cbar_quiver_kw = {}

    # Step 3: If `target_type` is `quiver`, find the `quiver` colorbar, copy parameters, and apply them to a duplicate
    if target_type == 'quiver':
        quiver_cbar_props = {}

        # Search for the quiver colorbar in ax.collections
        for collection in ax.collections:
            if hasattr(collection, 'colorbar') and collection.colorbar is not None:
                quiver_cbar_props = {
                    'mappable': collection,
                    'cmap': collection.cmap,
                    'ax': collection.colorbar.ax,
                    'tick_values': collection.colorbar.get_ticks(),
                    'tick_labels': [label.get_text() for label in collection.colorbar.ax.get_xticklabels()]
                }
                fig.delaxes(collection.colorbar.ax)  # Remove the old quiver colorbar
                break

        if not quiver_cbar_props:
            raise ValueError("No quiver colorbar found to transfer properties.")

        # Set up a new colorbar axis for the `quiver` colorbar (e.g., above the plot)
        cax_quiver = ax_divider.append_axes(cbar_quiver_kw.get('location', 'right'),
                                            size=cbar_quiver_kw.get('size', 0.2),
                                            pad=cbar_quiver_kw.get('pad', 0.5))

        # Create a new colorbar using the `quiver` mappable and apply `quiver`-specific properties
        new_quiver_cbar = fig.colorbar(
            quiver_cbar_props['mappable'],
            cax=cax_quiver,
            label=cbar_quiver_kw.get('ylabel', 'Parameter'),
            orientation=cbar_quiver_kw.get('orientation', 'vertical', ),
            aspect='auto',
            fraction=0.15,
            shrink=1.0,
            extend='neither',
            extendrect=False,
            #format='%.2f',
            ticks=mpl_ticker.MaxNLocator(nbins='auto', prune=None, min_n_ticks=3)
        )

        # Apply the `quiver` colormap and tick properties manually
        #new_quiver_cbar.mappable.set_cmap(quiver_cbar_props['cmap'])
        for cbar in [new_quiver_cbar]:
            if cbar is not None:
                # class ScalarFormatterClass(mpl_ticker.ScalarFormatter):
                #    def _set_format(self):
                #        self.format = f"%{.1}f"

                xScalarFormatter = mpl_ticker.ScalarFormatter(useOffset=True, useMathText=True)
                xScalarFormatter.set_powerlimits((-1, 1))
                xScalarFormatter.set_scientific(True)
                xScalarFormatter._offset_threshold = 2
                xScalarFormatter._scientific = True
                cbar.ax.xaxis.set(major_formatter=xScalarFormatter)
                plt.draw()

                # formatter_dict = yScalarFormatter.__dict__
                # print("ScalarFormatter __dict__ contents:")
                # for key, value in formatter_dict.items():
                #    print(f"{key}: {value}")

                label_offset_text = cbar_quiver_kw.get('ylabel', 'Parameter')
                label_offset_text += f' ($\\mathdefault{{10^{{{xScalarFormatter.orderOfMagnitude}}}}}$)'
                label_offset_text += f' + {xScalarFormatter.offset}' if xScalarFormatter.offset != 0 else ''

                cbar.set_label(label=label_offset_text,
                               loc='center',
                               rotation=180 if cbar_imshow_kw.get('location', 'bottom') == 'bottom' else 0,
                               labelpad=20 if cbar_imshow_kw.get('location', 'bottom') == 'bottom' else 2,
                               fontsize=cbar.ax.yaxis.label.get_fontsize() - 2
                               )

                cbar.ax.xaxis.get_offset_text().set_visible(False)

    # Step 5: Apply additional x-axis and y-axis settings if provided
    if cbar_xaxis_kw:
        new_imshow_cbar.ax.xaxis.set(**cbar_xaxis_kw)
    if cbar_yaxis_kw:
        new_imshow_cbar.ax.yaxis.set(**cbar_yaxis_kw)

    for cbar in [new_imshow_cbar]:
        if cbar is not None:
            #class ScalarFormatterClass(mpl_ticker.ScalarFormatter):
            #    def _set_format(self):
            #        self.format = f"%{.1}f"

            yScalarFormatter = mpl_ticker.ScalarFormatter(useOffset=True, useMathText=True)
            yScalarFormatter.set_powerlimits((-2, 2))
            yScalarFormatter.set_scientific(True)
            yScalarFormatter._offset_threshold = 2
            yScalarFormatter._scientific = True
            cbar.ax.yaxis.set(major_formatter=yScalarFormatter)
            plt.draw()

            #formatter_dict = yScalarFormatter.__dict__
            #print("ScalarFormatter __dict__ contents:")
            #for key, value in formatter_dict.items():
            #    print(f"{key}: {value}")

            label_offset_text = imshow_cbar_props.get('ylabel', 'Parameter')
            label_offset_text += f' ($\\mathdefault{{10^{{{yScalarFormatter.orderOfMagnitude}}}}}$)'
            label_offset_text += f' + {yScalarFormatter.offset}' if yScalarFormatter.offset != 0 else ''

            cbar.set_label(label=label_offset_text,
                           loc='center',
                           rotation=270 if cbar_imshow_kw.get('location', 'right') == 'right' else 90,
                           labelpad=24 if cbar_imshow_kw.get('location', 'right') == 'right' else 2,
                           fontsize=cbar.ax.yaxis.label.get_fontsize() - 2
                           )

            cbar.ax.yaxis.get_offset_text().set_visible(False)
