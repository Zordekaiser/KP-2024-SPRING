from sc_client.client import template_search, check_elements
import logging
from sc_client.constants import sc_types
from sc_client.models import ScTemplate, ScAddr
from sc_kpm.utils import get_system_idtf, get_link_content_data
from sc_kpm import ScKeynodes, ScAgentClassic, ScResult
from sc_kpm.utils.action_utils import (
    create_edge,
    finish_action_with_status,
)
from sc_kpm.sc_sets import ScStructure

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(name)s | %(message)s", datefmt="[%d-%b-%y %H:%M:%S]"
)

class ReplyToMessagesAgent(ScAgentClassic):
    def __init__(self):
        super().__init__("action_reply_to_messages")
        print('init_suc')

    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        print('event_start')
        result = self.processing(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("ConfigSettingsAgent finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result

    def processing(self, action_node: ScAddr):
        action_node = ScKeynodes["action_node"]
        struct_input = self.search_one_triple_with_role_relation(action_node, ScKeynodes["rrel_1"])
        temp_input = self.search_one_triple_with_role_relation(action_node, ScKeynodes["rrel_2"])
        struct_addrs = self.search_triple(struct_input)
        temp_addrs = self.search_triple(temp_input)

        var_map = self.mapping(temp_addrs)
        const_map = self.mapping(struct_addrs)

        filtered_struct_addrs = self.comparison(var_map, const_map)
        sc_struct = ScStructure()
        filt_edges_addrs = []
        for i in filtered_struct_addrs:
            for j in filtered_struct_addrs:
                buf = self.add_edge(i[0], j[0])
                if buf:
                    filt_edges_addrs.append(buf)
        for i in filtered_struct_addrs:
            for j in filt_edges_addrs:
                buf = self.add_edge(i[0], j)
                if buf:
                    filt_edges_addrs.append(buf)
        for i in filtered_struct_addrs:
            sc_struct.add(i[0])
        for i in filt_edges_addrs:
            sc_struct.add(i)
        create_edge(sc_types.EDGE_D_COMMON_CONST, action_node, sc_struct.set_node)
        return ScResult.OK

    def check_edge(self, input, target):
        example_template = ScTemplate()
        example_template.triple(input,
                                sc_types.UNKNOWN,
                                target)
        search_result = template_search(example_template)
        return len(search_result) != 0

    def add_edge(self, input, target):
        example_template = ScTemplate()
        example_template.triple(input,
                                sc_types.UNKNOWN >> 'edge',
                                target)
        search_result = template_search(example_template)
        if len(search_result) == 0:
            example_template.triple(target,
                                    sc_types.UNKNOWN >> 'edge',
                                    input)
            search_result = template_search(example_template)
            if len(search_result) == 0:
                return None
            else:
                return search_result[0].get('edge')
        else:
            return search_result[0].get('edge')

    def check_node(self, node):
        result = []

        result.append(node)
        result.append(check_elements(node)[0].is_node())
        result.append(check_elements(node)[0].is_class())
        result.append(check_elements(node)[0].is_role())
        result.append(check_elements(node)[0].is_norole())
        if check_elements(node)[0].is_node() or check_elements(node)[0].is_class() or check_elements(node)[
            0].is_role() or check_elements(node)[0].is_norole():
            return result
        else:
            return None

    def mapping(self, nodes):
        buffer_map = []
        buffer_nodes = []
        for i in nodes:
            buf = self.check_node(i)
            qwe = self.check_node(i)
            if buf != None:
                buffer_nodes.append(qwe)
                buffer_map.append(buf)
        result = []

        for i in range(len(buffer_nodes)):
            buffer = buffer_map[i]
            vertex = []
            for j in buffer_nodes:

                if self.check_edge(buffer_nodes[i][0], j[0]) or self.check_edge(j[0], buffer_nodes[i][0]):
                    vertex.append(j)
            buffer.append(vertex)
            result.append(buffer)
        return result

    def search_one_triple_with_role_relation(self, input: ScAddr, relation: ScAddr):
        result = None
        example_template = ScTemplate()
        example_template.triple_with_relation(input,
                                              sc_types.UNKNOWN,
                                              sc_types.NODE_VAR_STRUCT >> 'target',
                                              sc_types.UNKNOWN,
                                              relation)
        search_result = template_search(example_template)
        for i in search_result:
            result = i.get('target')
        return result

    def search_one_triple_with_relation_reverse(self, input: ScAddr, relation: ScAddr):
        result = None
        example_template = ScTemplate()
        example_template.triple_with_relation(sc_types.NODE >> 'target',
                                              sc_types.UNKNOWN,
                                              input,
                                              sc_types.UNKNOWN,
                                              relation >> 'rel')
        search_result = template_search(example_template)
        for i in search_result:
            result = i.get('target')
        return result

    def search_triple(self, input: ScAddr):
        result = []
        example_template = ScTemplate()
        example_template.triple(input,
                                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                                sc_types.UNKNOWN >> 'target')
        search_result = template_search(example_template)
        for i in search_result:
            result.append(i.get('target'))
        return result

    def comparison(self, var, const):
        result = []
        buffer_const = self.comparison_nodes(var, const)
        for i in buffer_const:
            comparis = False
            for j in var:
                if self.comparison_node(j, i) and (len(self.comparison_nodes(j[5], i[5])) != 0 or j[5] == i[5]):
                    comparis = True
            if comparis:
                result.append(i)

        return result

    def comparison_nodes(self, var, const):
        result = []
        for i in const:
            comparis = False
            for j in var:
                if self.comparison_node(j, i):
                    comparis = True
                    break
            if comparis:
                result.append(i)
        return result

    def comparison_node(self, var, const):
        result = True
        for i in range(1, 4):
            if var[i] != const[i]: result = False
        return result
