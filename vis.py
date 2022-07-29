from collections import defaultdict

import dfa
import funcy as fn
import pydot
from IPython.display import SVG
from IPython.display import display
from IPython.display import HTML as html_print

# from diss.concept_classes.dfa_concept import remove_stutter


COLOR_ALIAS = {
    'black': 'black',
    'yellow': '#ffff00', 
    'red': '#ff8b8b',
    'blue': '#afafff', 
    'brown' : '#f4a460'
}

# COLOR_ALIAS = {
#     'black': 'black',
#     'a': '#ffff00', 
#     'b': '#ff8b8b',
#     'c': '#afafff', 
#     'd' : '#f4a460'
# }

def remove_stutter(graph: dfa.DFADict) -> None:
    for state, (_, kids) in graph.items():
        tokens = list(kids.keys())
        kids2 = {k: v for k, v in kids.items() if v != state}
        kids.clear()
        kids.update(kids2)


# adapted from the dfa library
def get_dot(dfa_):
    dfa_dict, init = dfa.dfa2dict(dfa_)
    remove_stutter(dfa_dict)
    g = pydot.Dot(rankdir="LR")

    nodes = {}
    for i, (k, (v, _)) in enumerate(dfa_dict.items()):
        shape = "doublecircle" if v else "circle"
        nodes[k] = pydot.Node(i+1, label=f"{k}", shape=shape, color="black", fontcolor="black")
        g.add_node(nodes[k])

    edges = defaultdict(list)
    for start, (_, transitions) in dfa_dict.items():        
        for action, end in transitions.items():
            color = COLOR_ALIAS[str(action)]
            edges[start, end].append(color)
    
    init_node = pydot.Node(0, shape="point", label="", color="black")
    g.add_node(init_node)
    g.add_edge(pydot.Edge(init_node, nodes[init], color="black"))

    for (start, end), colors in edges.items():
        #color_list = f':'.join(colors)
        #g.add_edge(pydot.Edge(nodes[start], nodes[end], color=color_list))
        for color in colors:
            g.add_edge(pydot.Edge(nodes[start], nodes[end], label='◼', fontcolor=color, color="black"))
    g.set_bgcolor("#00000000")        
    return g


def save_dfa_as_pdf(dfa, fname):
    pdot = get_dot(dfa)
    pdot.write_pdf(fname.split('.')[0] + '.pdf')


def tile(color='black'):
    color = COLOR_ALIAS.get(color, color)
    s = '&nbsp;'*4
    return f"<text style='border: solid 1px;background-color:{color}'>{s}</text>"


def ap_at_state(x, y, world):
    """Use sensor to create colored tile."""
    if (x, y) in world.overlay:
        color = world.overlay[(x,y)]

        if color in COLOR_ALIAS.keys():
            return tile(color)
    return tile('black')


def print_map(world):
    """Scan the board row by row and print colored tiles."""
    order = range(1, world.dim + 1)
    buffer = ''
    for y in order:
        chars = (ap_at_state(x, y, world) for x in order)
        buffer += '&nbsp;'.join(chars) + '<br>'
    display(html_print(buffer))


def print_trc(path, world, idx=0):
    actions = [s.action for s, kind in path if kind == 'env']
    states = [s for s, kind in path if kind == 'ego']
    obs = [ap_at_state(pos.x, pos.y, world) for pos in states]
    if len(actions) > len(obs):
        obs.append('')
    elif len(obs) > len(actions):
        actions.append('')
    trc = fn.interleave(obs, actions)

    display(html_print(f'trc {idx}:&nbsp;&nbsp;&nbsp;' + ''.join(trc)))

if __name__ == '__main__':
    # dfa_dict = {0: (False, {'a': 1}),
    #             1: (True, {'a':1})}
    # temp = dfa.utils.dict2dfa(dfa_dict, start=0)
    # save_dfa_as_pdf(temp, 'dfa_diss1.pdf')
    # dfa_dict = {0: (True, {'b': 1}),
    #             1: (False, {'b':1})}
    # temp = dfa.utils.dict2dfa(dfa_dict, start=0)
    # save_dfa_as_pdf(temp, 'dfa_diss2.pdf')
    # dfa_dict = {0: (True, {'c': 1, 'a':0, 'd':0}),
    #             1: (True, {'a':2, 'c':1, 'd':0}),
    #             2: (False, {'a':2, 'c':2, 'd':2})}
    # temp = dfa.utils.dict2dfa(dfa_dict, start=0)
    # save_dfa_as_pdf(temp, 'dfa_diss3.pdf')

    # dfa_dict = {0: (False, {'a': 1, 'b': 0}),
    #             1: (False, {'a': 1, 'b': 2}),
    #             2: (True, {'a': 2, 'b': 2})}
    # temp = dfa.utils.dict2dfa(dfa_dict, start=0)
    # save_dfa_as_pdf(temp, 'dfa1.pdf')
    # dfa_dict = {0: (False, {'c': 1, 'd': 0}),
    #             1: (False, {'c': 1, 'd': 2}),
    #             2: (True, {'c': 2, 'd': 2})}
    # temp = dfa.utils.dict2dfa(dfa_dict, start=0)
    # save_dfa_as_pdf(temp, 'dfa2.pdf')

    dfa_dict = {0: (False, {'yellow': 3, 'blue': 1, 'red': 2, 'brown': 0}),
                1: (False, {'yellow': 2, 'blue': 1, 'red': 2, 'brown': 0}),
                2: (False, {'yellow': 2, 'blue': 2, 'red': 2, 'brown': 2}),
                3: (True,  {'yellow': 3, 'blue': 3, 'red': 3, 'brown': 3})}
    temp = dfa.utils.dict2dfa(dfa_dict, start=0)
    save_dfa_as_pdf(temp, 'diss.pdf')







