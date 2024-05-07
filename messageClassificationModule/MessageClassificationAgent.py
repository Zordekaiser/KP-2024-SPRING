from sc_client.client import template_search, resolve_keynodes
import logging
from sc_client.constants import sc_types
from sc_client.models import ScTemplate, ScAddr, ScIdtfResolveParams
from sc_kpm.utils import get_system_idtf, get_link_content_data, create_edge, get_edge
from sc_kpm import ScKeynodes, ScAgentClassic, ScResult
from sc_kpm.utils.action_utils import (
    create_action_answer,
    finish_action_with_status,
    get_action_arguments,
    get_element_by_role_relation
)
from sc_kpm.sc_sets import ScStructure
from .rasa_script import connect_to_rasa

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(name)s | %(message)s", datefmt="[%d-%b-%y %H:%M:%S]"
)

class MessageClassificationAgent(ScAgentClassic):
    def __init__(self):
        super().__init__("action_message_classification")
        self.logger.info("123")

    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        print('event_start')
        result = self.processing(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("ConfigSettingsAgent finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result

    def processing(self, action_node: ScAddr):
        message_input = self.search_one_triple_with_role_relation(action_node, ScKeynodes["rrel_1"])
        empty_node = self.search_one_triple_with_relation_reverse(message_input, ScKeynodes["nrel_sc_text_translation"])
        link_with_message = self.search_link(empty_node)
        message_string = get_link_content_data(link_with_message)
        classified_string: str = connect_to_rasa(message_string)
        entity, question = self.split_str(classified_string)
        params = ScIdtfResolveParams(idtf=question, type=sc_types.NODE_CONST)
        addrs = resolve_keynodes(params)  # 0 - class of message, 1 - message, 2 - entity, 3 - class of entity, 4 - rrel_entity
        addrs_edges = []  # 0 - class of message -> message, 1 - message -> entity, 2 - entity <- 3, 3 - 1 <- rrel_entity
        addrs.append(message_input)  # 1
        addrs.append(ScKeynodes[entity])  # 2
        addrs_edges.append(create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, addrs[0], addrs[1]))  # 0
        addrs_edges.append(create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, addrs[1], addrs[2]))  # 1
        addrs.append(self.search_one_triple_reverse_class(addrs[2]))  # 3
        addrs.append(ScKeynodes["rrel_entity"])  # 4
        addrs_edges.append(get_edge(addrs[3], addrs[2], sc_types.EDGE_ACCESS_VAR_POS_PERM))  # 2
        addrs_edges.append(create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, addrs[4], addrs_edges[1]))  # 3
        print(addrs_edges[3])
        sc_struct = ScStructure()
        for i in addrs:
            sc_struct.add(i)
        for i in addrs_edges:
            sc_struct.add(i)
        create_edge(sc_types.EDGE_D_COMMON_CONST, action_node, sc_struct.set_node)
        return ScResult.OK

    def split_str(self, string: str):
        buffer_array = string.split(", ")
        return buffer_array[0], buffer_array[1]

    def search_one_triple_with_role_relation(self, input: ScAddr, relation: ScAddr):
        result = None
        example_template = ScTemplate()
        example_template.triple_with_relation(input,
                                              sc_types.UNKNOWN,
                                              sc_types.NODE >> 'target',
                                              sc_types.UNKNOWN,
                                              relation >> 'rel')
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

    def search_one_triple(self, input: ScAddr):
        result = None
        example_template = ScTemplate()
        example_template.triple(input,
                                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                                sc_types.NODE >> 'target')
        search_result = template_search(example_template)
        for i in search_result:
            result = i.get('target')
        return result

    def search_link(self, input: ScAddr):
        result = None
        example_template = ScTemplate()
        example_template.triple(input,
                                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                                sc_types.LINK_VAR >> 'target')
        search_result = template_search(example_template)
        for i in search_result:
            result = i.get('target')
        return result

    def search_one_triple_reverse_class(self, input: ScAddr):
        result = None
        example_template = ScTemplate()
        example_template.triple(sc_types.NODE_VAR_CLASS >> 'target',
                                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                                input)
        search_result = template_search(example_template)
        for i in search_result:
            result = i.get('target')
        return result
