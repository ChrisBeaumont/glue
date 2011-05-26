import string
import atpy

import cloudviz
from cloudviz.io import extract_data_fits, extract_data_hdf5


class Component(object):

    def __init__(self, data, units=None):

        # The physical units of the data
        self.units = units

        # The actual data
        self.data = data


class Data(object):

    def __init__(self):
        # Coordinate conversion object
        self.coords = None

        # Number of dimensions
        self.ndim = None

        # Dataset shape
        self.shape = None

        # Components
        self.components = {}

        # Tree description of the data
        self.tree = None

        # Subsets of the data
        self.subsets = []

        # Hub that the data is attached to
        self._hub = None

    def new_subset(self):
        subset = cloudviz.Subset()
        self.add_subset(subset)
        return subset

    def add_subset(self, subset):
        subset.data = self
        subset.do_broadcast(True)
        self.subsets.append(subset)
        if self._hub is not None:
            self._hub.broadcast(subset, action='add')

    def remove_subset(self, subset):
        if self._hub is not None:
            self._hub.broadcast(subset, action='remove')
        self.subsets.pop(subset)

    def read_tree(self, filename):
        '''
        Read a tree describing the data from a file
        '''
        self.tree = cloudviz.Tree(filename)

    def __str__(self):
        s = ""
        s += "Number of dimensions: %i\n" % self.ndim
        s += "Shape: %s\n" % string.join([str(x) for x in self.shape], ' x ')
        s += "Components:\n"
        for component in self.components:
            s += " * %s\n" % component
        return s[:-1]

    def __setattr__(self, name, value):
        if name == "hub" and hasattr(self, 'hub') \
           and self._hub is not value and self._hub is not None:
            raise AttributeError("Data has already been assigned "
                                 "to a different hub")
        object.__setattr__(self, name, value)


class TabularData(Data):
    '''
    A class to represent any form of tabular data. We restrict
    ourselves to tables with 1D columns.
    '''

    def read_data(self, *args, **kwargs):
        '''
        Read a table from a file or database. All arguments are passed to
        ATpy.Table(...).
        '''

        # Read the table
        table = atpy.Table(*args, **kwargs)

        # Loop through columns and make component list
        for column_name in table.columns:
            c = Component(table[column_name],
                          units=table.columns[column_name].unit)
            self.components[column_name] = c

        # Set number of dimensions
        self.ndim = 1

        # Set data shape
        self.shape = len(table)


class GriddedData(Data):
    '''
    A class to represent uniformly gridded data (images, data cubes, etc.)
    '''

    def read_data(self, filename, format='auto'):
        '''
        Read n-dimensional data from `filename`. If the format cannot be
        determined from the extension, it can be specified using the
        `format=` option. Valid formats are 'fits' and 'hdf5'.
        '''

        # Try and automatically find the format if not specified
        if format == 'auto':
            if filename.lower().endswith('.gz'):
                format = filename.lower().rsplit('.', 2)[1]
            else:
                format = filename.lower().rsplit('.', 1)[1]

        # Read in the data
        if format in ['fits', 'fit']:
            arrays = extract_data_fits(filename)
            for component_name in arrays:
                self.components[component_name] = \
                    Component(arrays[component_name])
        elif format in ['hdf', 'hdf5', 'h5']:
            arrays = extract_data_hdf5(filename)
            for component_name in arrays:
                self.components[component_name] = \
                    Component(arrays[component_name])
        else:
            raise Exception("Unkonwn format: %s" % format)

        # Set number of dimensions
        self.ndim = self.components[self.components.keys()[0]].data.ndim

        # Set data shape
        self.shape = self.components[self.components.keys()[0]].data.shape


class AMRData(Data):
    pass
