import dataclasses
import inspect
import json
import os
from typing import Any, Dict


def _get_flow_file() -> str:
    flow_file = os.environ.get('FLOW_FILE')
    if flow_file is None:
        # TODO: maybe we could try and parse this out if it's not set? My main
        # worry is that it feels brittle and might break easily
        # Maybe we can walk backwards till we find the correct file?
        raise ValueError(
            'Could not determine flow file. Please set the FLOW_FILE '
            'environment variable to point to the flow that is running. If you'
            ' using the LaunchFlow extension this should happen automatically.'
        )
    return flow_file


def _read_flow_config() -> Dict[str, Any]:
    flow_file = _get_flow_file()
    with open(flow_file, 'r', encoding='UTF-8') as f:
        flow = json.load(f)
    return flow


def _get_node_space_from_module() -> str:
    frm = inspect.stack()[1]
    mod = inspect.getmodule(frm[0])
    mod_name = mod.__name__
    return mod_name.replace('.', '/')


@dataclasses.dataclass
class _NodeInfo:
    node_space: str
    incoming_node_spaces: str
    outgoing_node_spaces: str
    node_config: str


def _get_node_info(node_space: str) -> _NodeInfo:
    flow = _read_flow_config()
    node = None
    for n in flow['nodes']:
        if n['nodeSpace'] in node_space:
            node = n
            break
    if node is None:
        raise ValueError(
            f'Unable to find node for calling module: {node_space}')

    outgoing_node_spaces = flow['outgoingEdges'].get(node['nodeSpace'], [])
    incoming_node_spaces = []
    for incoming, nodes in flow['outgoingEdges'].items():
        if node['nodeSpace'] in nodes:
            incoming_node_spaces.append(incoming)
    flow_file = _get_flow_file()
    print('DO NOT SUBMIT: ', flow_file)
    base_path = flow_file.replace('flow_state.json', '')
    config_file = os.path.join(base_path, node['nodeSpace'], 'config.json')
    with open(config_file, mode='r', encoding='UTF-8') as f:
        config = json.load(f)
    return _NodeInfo(node['nodeSpace'], incoming_node_spaces,
                     outgoing_node_spaces, config)
