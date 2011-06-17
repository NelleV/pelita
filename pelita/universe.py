from collections import Mapping

wall   = '#'
food   = '.'
harvester = 'c'
destroyer = 'o'
free   = ' '

layout_chars = [wall, food, harvester, destroyer, free]

north = 'NORTH'
south = 'SOUTH'
west  = 'WEST'
east  = 'EAST'
stop  = 'STOP'

move_ids = [north, south, east, west, stop]

def new_positions(current):
    """ Determine where a move will lead.

    Parameters
    ----------
    current : int, int
        current position

    Returns
    -------
    new_pos : dict 
        mapping of moves (str) to new_positions (int,int)

    """
    return {
        north : (current[0]-1, current[1]),
        south : (current[0]+1, current[1]),
        west  : (current[0], current[1]-1),
        east  : (current[0], current[1]+1),
        stop  : (current[0], current[1])}

class LayoutEncodingException(Exception):
    pass

def check_layout(layout_str, number_bots):
    """ Check the legality of the layout string.

    Parameters
    ----------
    layout_str : str
        the layout string
    number_bots : int
        the total number of bots that should be present

    Raises
    ------
    LayoutEncodingException
        if an illegal character is encountered
    LayoutEncodingException
        if a bot-id is missing
    LayoutEncodingException
        if a bot-id is specified twice

    """
    bot_ids = [str(i) for i in range(number_bots)]
    existing_bots = []
    legal = layout_chars + bot_ids  + ['\n']
    for c in layout_str:
        if c not in legal:
            raise LayoutEncodingException(
                "Char: '%c' is not a legal layout character" % c)
        if c in bot_ids:
            if c in existing_bots:
                raise LayoutEncodingException(
                    "Bot-ID: '%c' was specified twice" % c)
            else:
                existing_bots.append(c)
    if bot_ids != existing_bots:
        missing = [str(i) for i in set(bot_ids).difference(set(existing_bots))]
        missing.sort()
        raise LayoutEncodingException(
            'Layout is invalid for %i bots, The following IDs were missing: %s '
            % (number_bots, missing))
    lines = layout_str.split('\n')
    for i in range(len(lines)):
        if len(lines[i]) != len(lines[0]):
            raise LayoutEncodingException(
                'The layout must be rectangular,'+\
                'line %i has length %i instead of %i'
                % (i, len(lines[i]), len(lines[0])))

def strip_layout(layout_str):
    """ Remove leading and trailing whitespace from a string encoded layout.

    Parameters
    ----------
    layout_str : str
        the layout, possibly with whitespace

    Returns
    -------
    layout_str : str
        the layout with whitespace removed

    """
    return '\n'.join([line.strip() for line in layout_str.split('\n')])

def layout_shape(layout_str):
    """ Determine shape of layout.

    Parameters
    ----------
    layout_str : str
        a checked layout string

    Returns
    -------
    height : int
    width : int

    """
    return (len(layout_str.split('\n')), layout_str.find('\n'))

class Mesh(Mapping):
    """ More or less a Matrix.

    Using a list of lists to represent a matrix is memory inefficient and slow
    (and ugly). Instead we store the matrix data in a single list and provide
    accessors methods (__getitem__() and __setitem__()) to access the elements
    in a matrixy style.

    Attributes
    ----------
    height : int
    width : int
    shape : (int, int)

    Parameters
    ----------
    height : int
    width : int

    Notes
    -----
    Once the container has been allocated, it cannot be resized.

    The container can store arbitrary type objects and even mix types.

    The constructor will preallocate a container with an appropriate shape, and
    populate this with `None`.

    The container cannot be sliced.

    Examples
    --------
    >>> m = Mesh(2,2)
    >>> print m
    [None, None]
    [None, None]
    >>> m[0,0] = True
    >>> m[1,1] = True
    >>> print m
    [True, None]
    [None, True]
    >>> m[0,1] = 'one'
    >>> m[1,0] = 1
    >>> print m
    [True, 'one']
    [1, True]
    >>> for i in m: print i
    True
    one
    1
    True
    """

    def __init__(self, height, width):
        self.height = height
        self.width = width
        self.shape = (height, width)
        self._data = [None for i in range(self.width * self.height)]

    def _check_index(self, index):
        if index[0] >= self.height or index[0] < 0:
            raise IndexError(
                    'Mesh indexing error, requested row: %i, but height is: %i'
                    % (index[0], self.height))
        elif index[1] >= self.width or index[1] < 0:
            raise IndexError(
                    'Mesh indexing error, requested column: %i, but width is: %i'
                    % (index[1], self.height))

    def __getitem__(self, index):
        self._check_index(index)
        return self._data[index[0] * self.width + index[1]]

    def __setitem__(self, index, item):
        self._check_index(index)
        self._data[index[0] * self.width + index[1]] = item

    def __iter__(self):
        return self._data.__iter__()

    def __len__(self):
        return self.height * self.width

    def __str__(self):
        output = str()
        for i in range(self.height):
            start = i*self.width
            end = start + self.width
            output += str(self._data[start:end])
            output += '\n'
        return output

def convert_to_grid(layout_str):
    """ Convert a layout string to a list of lists.

    Parameters
    ----------
    layout_str : str
        a checked layout string

    Returns
    -------
    layout : list of lists of chars
    """
    return [[c for c in l.strip()] for l in layout_str.split('\n')]

def initial_positions(layout_grid, shape, number_bots):
    """ Extract initial positions from layout.

    Also replaces the initial positions with free spaces.

    Parameters
    ----------
    layout_grid : list of list of chars
        the layout in grid format
    shape : int, int
        height and width of the grid
    number_bots : int
        the number of bots for which to find initial positions

    Returns
    -------
    initial pos : list of tuples
        the initial positions for all the bots
    """
    bot_ids = [str(i) for i in range(number_bots)]
    start = [(0, 0)] * number_bots
    height, width = shape[0], shape[1]
    for (h,w) in ((h,w) for h in range(height) for w in range(width)):
        if layout_grid[h][w] in bot_ids:
            start[int(layout_grid[h][w])] = (h,w)
            layout_grid[h][w] = ' '
    return start

def extract_food(layout_grid, shape):
    """ Extract positions of food.

    Also replaces the food positions with free spaces.

    Parameters
    ----------
    layout_grid : list of list of chars
        the layout in grid format
    shape : int, int
        height and width of the grid

    Returns
    -------
    food : list of list of booleans

    """
    height, width = shape[0], shape[1]
    food_grid = [[False for i in range(width)] for j in range(height)]
    for (h,w) in ((h,w) for h in range(height) for w in range(width)):
        if layout_grid[h][w] == food:
            food_grid[h][w] = True
            layout_grid[h][w] = ' '
    return food_grid

class Universe(object):

    def __init__():
        pass

    def init_bots():
        pass

    def get_number_bots():
        pass

class Universe(object):
    """ The Universe: representation of the game state.

    Attributes
    ----------
    initial_layout : str
        initial layout with food and agent positions
    number_bots : int
        total number of bots
    width : int
        width (number of columns)
    height : int
        height (nuber rows)
    shape : int, int
        width and height (in that order)
    layout : list of lists of characters
        static layout (free spaces and walls only)
    initial_pos : list of (int, int)
        the initial positions for the bots
    bot_positions : list of (int, int)
        the current positions of the bots
    food_positions : list of lists of booleans
        the current food positions

    Parameters
    ----------
    layout_str : str
        the layout for this universe
    number_bots : int
        the number of bots for this universe
    """
    def __init__(self, layout_str, number_bots):
        self.initial_layout = strip_layout(layout_str)
        self.number_bots = number_bots
        check_layout(self.initial_layout, self.number_bots)
        self.width, self.height = layout_shape(self.initial_layout)
        self.shape = (self.width, self.height)
        self.layout = convert_to_grid(self.initial_layout)
        self.initial_pos = initial_positions(self.layout, self.shape, self.number_bots)
        self.bot_positions = self.initial_pos
        self.food_positions = extract_food(self.layout, self.shape)

    def reset_bot(index):
        pass

if __name__ == "__main__":
    pass
