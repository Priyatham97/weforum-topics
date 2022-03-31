import json
import pandas as pd
import networkx as nx
import streamlit as st
from pathlib import Path
from pyvis.network import Network
from streamlit.components import v1 as components

FILE_DIR = Path(__file__).parent.absolute()
KI_KEYWORD = "-keyissue"


@st.cache()
def load_data():
    with open(FILE_DIR / 'data/topics.json') as f:
        data = json.load(f)
    return data


def build_adj_list(data):
    adj_list = {}
    for datum in data:
        parent = list(datum.keys())[0]
        descendants = list(datum.values())[0]['children']
        for descendant in descendants:
            try:
                adj_list[parent].append(descendant['child'])
            except KeyError:
                adj_list[parent] = [descendant['child']]
            for gchild in descendant['gchild']:
                try:
                    adj_list[descendant['child']].append(gchild)
                except KeyError:
                    adj_list[descendant['child']] = [gchild]

    for datum in data:
        parent = list(datum.keys())[0]
        descendants = list(datum.values())[0]['children']
        # if parent == ''
        for descendant in descendants:
            if descendant['child'] == 'Corporate Governance' \
            and  'Emerging-Market Multinationals' in descendant['gchild']:
                print(parent, descendant)

    adj_list = {k: sorted(set(v)) for k, v in adj_list.items()}
    adj_list['Corporate Governance']
    return


@st.cache(allow_output_mutation=True)
def build_graph(data):

    edges = []
    topics = []
    for datum in data:
        parent = list(datum.keys())[0]
        topics.append(parent)
        descendants = list(datum.values())[0]['children']
        for descendant in descendants:
            edges.append((parent, f"{descendant['child']}{KI_KEYWORD}"))
            for gchild in descendant['gchild']:
                edges.append((f"{descendant['child']}{KI_KEYWORD}", gchild))
    edges = list(set(edges))

    G = nx.DiGraph()
    G.add_edges_from(edges)
    return G, sorted(topics)


def customize_nodes(network, node_id, color='red'):
    network.get_node(node_id)['size'] = 20
    network.get_node(node_id)['color'] = color
    network.get_node(node_id)['font']['size'] = 15


def render_paths(_paths, topic_a, topic_b):

    g_edges = []
    for path in _paths:
        g_edges.extend([(path[i], path[i + 1]) for i in range(len(path) - 1)])
    g_edges = list(set(g_edges))

    g = nx.DiGraph()
    g.add_edges_from(g_edges)

    plot_h, plot_w = 400, 800
    net = Network(height=f'{plot_h}px', width=f'{plot_w}px', font_color='#ffffff', bgcolor='#000000')
    net.from_nx(g)
    customize_nodes(net, topic_a, color='red')
    customize_nodes(net, topic_b, color='green')

    # Generate network with specific layout settings
    net.repulsion(node_distance=420, central_gravity=0.33, spring_length=110, spring_strength=0, damping=0.35)

    # Save and read graph as HTML file
    spath = str(FILE_DIR / 'tmp/pyvis_graph.html')
    net.save_graph(spath)
    with open(spath, 'r', encoding='utf-8') as f:
        components.html(f.read(), height=plot_h, width=plot_w)


def render_stats(_paths):
    col_a, col_b = st.columns(2)
    col_a.header(f'Total Paths:{len(_paths)}')
    df = pd.DataFrame([len(f) for f in _paths])
    df.columns = ['paths_count']
    col_b.dataframe(
        pd.DataFrame(df['paths_count'].value_counts()).reset_index().rename(columns={
            'index': 'Path Length',
            'paths_count': 'No. of paths'
        }))


def clean(text):
    return text.replace(KI_KEYWORD, '')


def main():

    data = load_data()
    G, topics = build_graph(data)

    # drpdwn_a, drpdwn_b = st.sidebar.columns(2)
    topic_a = st.sidebar.selectbox('Select a topic A', topics)
    topic_b = st.sidebar.selectbox('Select a topic B', topics)

    cutoff = st.sidebar.slider('Cutoff', 0, 10, 5)
    _paths = list(nx.all_simple_paths(G, topic_a, topic_b, cutoff=cutoff))
    if _paths:
        render_stats(_paths)
        render_paths(_paths, topic_a, topic_b)
        if st.button("Show all paths"):
            st.table([' → '.join(map(clean, path)) for path in sorted(_paths, key=len)])
    else:
        st.write('No paths found')


if __name__ == '__main__':
    main()
